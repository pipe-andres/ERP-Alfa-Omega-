# Category System - Fase 2

Documento técnico del nuevo sistema de categorías y atributos dinámicos.

Estructura de tablas nuevas (compatibles):
- `categories(id, parent_id, name, slug)`
- `category_attributes(id, category_id, attr_name, attr_type, attr_options)`
- `product_attributes(id, product_code, attr_name, attr_value)`

Funciones expuestas por `src/services/categories_service.py`:
- `get_categories_tree()`
- `get_category_filters(category_id)`
- `filter_products(category_id, filters)`
- `build_breadcrumbs(category_id)`
- `attach_attributes_to_product(product)`

Recomendaciones DB:
- Añadir índices: `categories(name)`, `product_attributes(product_code, attr_name)` para acelerar filtros.
- Migrar attributes a JSON si la DB lo soporta.

Integración con UI:
- Proveer panel lateral con árbol de categorías (usar `get_categories_tree`).
- Render filtros dinámicos usando `get_category_filters`.
- Al aplicar filtros, llamar a `filter_products`.

