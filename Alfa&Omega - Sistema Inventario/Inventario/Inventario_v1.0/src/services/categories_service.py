"""Servicio de categorías profesional.
Provee árbol de categorías, filtros, búsqueda por atributos y helpers para UI.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional

from src.database import repository
from src.core import caching
from src.models.category import Category

# Asegura esquema al importar
repository.ensure_schema()


@caching.cached(ttl=300)
def get_categories_tree() -> List[Dict[str, Any]]:
    raw = repository.get_categories_tree()
    return raw


def get_category_filters(category_id: int) -> Dict[str, Any]:
    # devuelve atributos dinámicos para filtros (nombre, tipo, opciones)
    attrs = repository.get_category_attributes(category_id)
    # map to filter format
    filters = {}
    for a in attrs:
        name = a.get('name')
        filters[name] = {'type': a.get('type'), 'options': a.get('options')}
    return filters


def build_breadcrumbs(category_id: int) -> List[Dict[str, Any]]:
    # simple climb-up
    crumbs: List[Dict[str, Any]] = []
    cur = repository.get_category_by_id(category_id)
    while cur:
        crumbs.insert(0, {'id': cur['id'], 'name': cur['name']})
        pid = cur.get('parent_id')
        cur = repository.get_category_by_id(pid) if pid else None
    return crumbs


def attach_attributes_to_product(product_code: str, attributes: Dict[str, str]) -> None:
    for k, v in attributes.items():
        repository.attach_attribute_to_product(product_code, k, v)


@caching.cached(ttl=60)
def filter_products(category_id: int, filters: Dict[str, Any], limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """Filter products by category and attribute filters. Returns list of product tuples.
    filters: {'marca':['Nike'],'color':['rojo'], 'talla':['M']}
    """
    # Build where clauses joining product_attributes
    where_clauses = []
    params: List[Any] = []
    if category_id:
        # simple category inclusion: products whose categoria equals category name or descendants
        cat = repository.get_category_by_id(category_id)
        if cat:
            where_clauses.append("LOWER(productos.categoria) = ?")
            params.append(cat['name'].lower())
    # attribute filters (AND semantics)
    i = 0
    for attr, vals in filters.items():
        i += 1
        placeholder = ":attr_" + str(i)
        # inner select checks existence
        clause = f"EXISTS(SELECT 1 FROM product_attributes pa WHERE pa.product_code = productos.codigo AND pa.attr_name = ? AND pa.attr_value IN ({','.join(['?']*len(vals))}))"
        where_clauses.append(clause)
        params.append(attr)
        params.extend(vals)
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    rows = repository.list_products(limit=limit, offset=offset, where_sql=where_sql, params=params)
    return [dict(codigo=r[0], nombre=r[1], categoria=r[2], precio=r[3], cantidad=r[4]) for r in rows]
