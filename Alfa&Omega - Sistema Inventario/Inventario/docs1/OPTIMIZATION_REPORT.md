# Optimization Report - Fase 2

## Objetivo
Mejorar rendimiento y mantenibilidad preservando funcionalidad.

## Cambios clave
- Caché in-memory para consultas frecuentes: `src/core/caching.py`
- Repository centralizado que evita SELECT en loops y ofrece funciones reutilizables: `src/database/repository.py`
- Models dataclass para validación ligera: `src/models/*`
- Categorías con atributos dinámicos y filtros combinables: `src/services/categories_service.py`
- UI components y theme actualizado para modo oscuro/claro
- Tests automatizados (pytest)

## Recomendaciones
1. Revisar queries pesadas y aplicar índices en BD (p.ej. `productos(categoria)`, `product_attributes(product_code, attr_name)`).
2. Para producción, migrar caching a Redis si la app se escala horizontalmente.
3. Considerar migración a bcrypt cuando `bcrypt` sea instalable de forma consistente.

## Métricas iniciales
- Caché de producto por 120s
- Caché de categorías por 300s

## Limitaciones
- Revisión manual recomendada: integración completa en GUI (usar nuevos componentes UI). No se han sustituido todas las llamadas en `main_window.py` para evitar romper la UI.

