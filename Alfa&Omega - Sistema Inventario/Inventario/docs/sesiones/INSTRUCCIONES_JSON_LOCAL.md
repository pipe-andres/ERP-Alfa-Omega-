# 🎯 Almacenamiento Local en JSON

El sistema ha sido completamente migrado para utilizar **almacenamiento local en archivos JSON** en lugar de una base de datos MySQL/PostgreSQL.

## 📁 Estructura de almacenamiento

Los datos se guardan como archivos JSON en el directorio `src/data/`:

```
src/
  data/
    productos.json      # Inventario de productos
    doc_series.json     # Series de numeración para documentos
    users.json          # (si se implementa)
    roles.json          # (si se implementa)
    partners.json       # (si se implementa)
    (más tablas...)
```

## ⚙️ Configuración

El archivo `.env` ya está configurado con:

```env
DB_ENGINE=json
DB_JSON_DIR=./src/data
```

**No es necesario tener una base de datos PostgreSQL o MySQL instalada.** Todo funciona localmente con archivos JSON.

## 🚀 Cómo usar

### Iniciar la aplicación:

```powershell
cd "c:\Users\ADMIN\Desktop\VS Code - Projects\Alfa&Omega - Sistema Inventario\Inventario"
python main.py
```

### Operaciones soportadas:

✅ **Productos:**
- Crear nuevo producto (con cualquier código: números, letras, símbolos)
- Editar producto existente
- Eliminar producto
- Listar/buscar productos
- Filtrar por código, nombre o categoría

✅ **Documentos:**
- Numeración automática por serie (PURCHASE, SALE, etc.)
- Gestión de series personalizadas

✅ **General:**
- Búsqueda y filtrado por campos
- Paginación de listados
- Validación de datos

## 📊 Formato de los datos

Los archivos JSON tienen un formato simple y legible:

**productos.json:**
```json
[
  {
    "codigo": "P001",
    "nombre": "Producto 1",
    "categoria": "Electrónica",
    "precio": 150.50,
    "cantidad": 10,
    "avg_cost": 150.50
  },
  {
    "codigo": "P002",
    "nombre": "Producto 2",
    "categoria": "Ropa",
    "precio": 25.00,
    "cantidad": 50,
    "avg_cost": 25.00
  }
]
```

**doc_series.json:**
```json
[
  {
    "doc_type": "PURCHASE",
    "series": "C01",
    "prefix": "C01-",
    "next_no": 5
  },
  {
    "doc_type": "SALE",
    "series": "V01",
    "prefix": "V01-",
    "next_no": 12
  }
]
```

## 🔄 Cambiar de motor de almacenamiento

Si en el futuro quieres volver a usar PostgreSQL u otra base de datos:

1. Abre `.env`
2. Cambia: `DB_ENGINE=postgres` (o `sqlite` o `mysql`)
3. Configura los detalles de conexión necesarios
4. Reinicia la aplicación

## ⚡ Ventajas del almacenamiento JSON

✨ **Sin dependencias externas** - No necesitas instalar ni configurar una base de datos

✨ **Portabilidad** - Los datos se transportan como archivos simples

✨ **Editable manualmente** - Puedes abrir `src/data/*.json` con cualquier editor de texto

✨ **Control total** - Los datos están en tu máquina local

✨ **Desarrollo rápido** - Ideal para pruebas y desarrollo sin infraestructura compleja

## 🛠️ Características implementadas

### En `src/services/inventory.py`:
- ✅ `add_product()` - Crear productos
- ✅ `update_product()` - Actualizar datos
- ✅ `delete_product()` - Eliminar
- ✅ `get_product()` - Obtener uno
- ✅ `list_products_page()` - Listar con paginación
- ✅ `count_products()` - Contar totales

### En `src/services/documents.py`:
- ✅ `ensure_schema()` - Inicializar
- ✅ `seed_default_series()` - Series por defecto
- ✅ `get_next_number()` - Numeración automática

### En `src/database/repository.py`:
- ✅ `get_product_by_code()` - Búsqueda
- ✅ `insert_product()` - Inserción
- ✅ `update_product_qty_price()` - Actualización
- ✅ `list_products()` - Listado
- ✅ `count_products()` - Conteo

## 📝 Notas importantes

- **Primero agrupa por páginas** - El sistema maneja paginación correctamente
- **Búsqueda insensible a mayúsculas** - "PROD" encuentra "prod", "Prod", "PROD"
- **Los cambios son persistentes** - Se guardan inmediatamente en los archivos JSON
- **No hay transacciones complejas** - Para casos simples está bien; si necesitas transacciones usa BD

## 🧪 Pruebas recomendadas

1. Abre la app: `python main.py`
2. Crea un nuevo producto con código numérico
3. Verifica que aparece en el listado
4. Edita el producto
5. Busca por código/nombre
6. Abre `src/data/productos.json` y verifica que los datos se guardaron

---

**¡Todo listo!** El sistema está configurado para usar almacenamiento local en JSON. 🎉
