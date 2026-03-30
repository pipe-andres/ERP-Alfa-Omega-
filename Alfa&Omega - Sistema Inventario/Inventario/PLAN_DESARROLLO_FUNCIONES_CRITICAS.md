# 🚀 PLAN DE ACCIÓN: FUNCIONES CRÍTICAS POR IMPLEMENTAR

**Prioridad:** ALTA - Estas funciones son IMPRESCINDIBLES antes de vender  
**Tiempo estimado:** 2-3 semanas para implementar las 5 principales  
**Generado:** 5 de marzo de 2026

---

## 🎯 TOP 5 FUNCIONES CRÍTICAS (Ordenadas por impacto)

---

## 1. 🔄 DEVOLUCIONES & REEMBOLSOS

### ¿Por qué es crítico?
- **Todos los negocios** necesitan gestionar devoluciones
- Si un cliente devuelve un producto, el sistema NO TIENE función para hacerlo
- El kardex quedaría inconsistente
- No hay audit trail de devoluciones

### Función propuesta: `post_return()`

```python
def post_return(
    numero: Optional[str],
    fecha: Optional[str],
    items: List[Dict],
    notas: Optional[str] = None,
    partner_code: Optional[str] = None,
    series: str = "D01",  # D = Devolución
    user_id: Optional[int] = None
) -> tuple[int, str]:
    """
    Registra una devolución/reverso de venta.
    
    items: [{codigo, qty, reason}]
    - Reversa la venta (devuelve stock al almacén)
    - Crea nota de crédito
    - Ajusta kardex automáticamente
    - Registra motivo de devolución
    
    Retorna: (doc_id, numero_devolucion)
    """
```

### Implementación mínima:
- ✅ UI para capturar devoluciones (nueva pestaña "🔄 Devoluciones")
- ✅ Captura: código, cantidad, motivo
- ✅ Genera número único (serie D01)
- ✅ Reversa venta anterior
- ✅ Actualiza kardex (entrada de stock)
- ✅ Genera nota de crédito en PDF
- ✅ Auditoría completa

### **Esfuerzo:** ~4 horas

---

## 2. 💰 DESCUENTOS & PROMOCIONES

### ¿Por qué es crítico?
- **Ninguna venta real** se hace a precio fijo
- Necesitas descuentos para:
  - Competir
  - Liquidar stock
  - Fidelizar clientes
  - Ofertas por temporada

### Funciones propuestas:

#### A) Descuento por Cliente
```python
def create_customer_discount(
    partner_code: str,
    discount_percent: float,
    product_codes: Optional[List[str]] = None,
    valid_from: str = None,
    valid_to: str = None
) -> int:
    """
    Asigna descuento a un cliente (global o por producto)
    """
```

#### B) Descuento por Volumen
```python
def get_volume_discount(
    cantidad: int,
    category: str = None
) -> float:
    """
    Retorna descuento % basado en cantidad
    Ej: 10+ unidades = 5%, 50+ unidades = 10%
    """
```

#### C) Promoción Temporal
```python
def create_promotion(
    product_code: str,
    discount_percent: float,
    start_date: str,
    end_date: str,
    max_quantity: Optional[int] = None
) -> int:
    """
    Define una promoción por período
    """
```

### Implementación en Ventas:
```python
# En post_sale(), calcular descuento:
discount = get_volume_discount(qty) + get_customer_discount(partner_code, codigo)
unit_price_final = unit_price * (1 - discount)
```

### **Esfuerzo:** ~6 horas

---

## 3. 📊 MARGEN DE GANANCIA & UTILIDAD

### ¿Por qué es crítico?
- **Director/Dueño necesita saber:** ¿cuánto ganamos?
- Sin margen, no se puede evaluar rentabilidad
- Sin rentabilidad por producto, no se sabe qué vender

### Funciones propuestas:

#### A) Cálculo de COGS (Cost of Goods Sold)
```python
def calculate_cogs(
    doc_id: int  # documento de venta
) -> Dict:
    """
    Retorna:
    {
        subtotal: 100.00,
        costo_total: 40.00,
        margen_bruto: 60.00,
        margen_pct: 60%,
        utilidad_neta: 45.00 (si restamos impuestos)
    }
    """
```

#### B) Rentabilidad por Producto
```python
def get_product_profitability(
    codigo: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> Dict:
    """
    Retorna:
    {
        total_vendido: 5000,
        costo_total: 2000,
        margen_total: 3000,
        margen_pct: 60%,
        cantidad_vendida: 100,
        precio_promedio: 50,
        costo_promedio: 20
    }
    """
```

#### C) Mostrar en Venta
```python
# En post_sale(), agregar a totals:
{
    "subtotal": ...,
    "costo_total": ...,
    "margen_bruto": ...,
    "margen_pct": ...
}
```

### **Esfuerzo:** ~3 horas

---

## 4. 📈 REPORTES AVANZADOS

### ¿Por qué es crítico?
- **CFO/Gerente necesita insights**
- Reportes actuales son muy básicos
- Sin análisis, no se pueden tomar decisiones

### Reportes a implementar:

#### A) Ventas por Período
```python
def report_sales_by_period(
    start_date: str,
    end_date: str,
    period: str = "daily"  # daily, weekly, monthly
) -> List[Dict]:
    """
    Retorna:
    [{
        period: "2026-03-01",
        total_sales: 5000,
        quantity: 50,
        avg_order: 100,
        margin: 3000
    }, ...]
    """
```

#### B) Análisis ABC (Pareto)
```python
def report_abc_analysis(
    months: int = 12
) -> Dict:
    """
    Clasifica productos en A (20%), B (30%), C (50%)
    Retorna:
    {
        "A": [{ codigo, ventas, pct }],
        "B": [...],
        "C": [...]
    }
    """
```

#### C) Productos Top Vendidos
```python
def report_top_products(
    limit: int = 10,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> List[Dict]:
    """
    Retorna top N productos por cantidad/ingresos
    """
```

#### D) Rotación de Inventario
```python
def report_inventory_rotation(
) -> Dict:
    """
    Calcula:
    - Turnover rate
    - Días para vender
    - Productos de lenta rotación
    """
```

### **Esfuerzo:** ~8 horas

---

## 5. 💳 CRÉDITO & TÉRMINOS DE PAGO

### ¿Por qué es crítico?
- **La mayoría de ventas B2B son a crédito**
- Sin gestión de crédito:
  - No sabes quién debe
  - No sabes cuándo cobrar
  - No hay seguimiento

### Funciones propuestas:

#### A) Definir Términos de Crédito
```python
def set_customer_credit_terms(
    partner_code: str,
    credit_limit: float,
    payment_terms: int = 30,  # días
    max_overdue: int = 60  # días máximo de atraso
) -> None:
    """
    Define términos de crédito para cliente
    """
```

#### B) Registrar Pago Parcial
```python
def record_payment(
    doc_id: int,
    amount: float,
    payment_method: str = "cash",
    fecha: Optional[str] = None,
    notas: Optional[str] = None
) -> int:
    """
    Registra pago de una factura
    Retorna payment_id
    """
```

#### C) Cuotas Automáticas
```python
def create_installment_plan(
    doc_id: int,
    num_cuotas: int,
    first_due_date: str,
    periodicity: str = "monthly"
) -> List[Dict]:
    """
    Divide factura en cuotas
    Retorna: [{cuota_no, amount, due_date}, ...]
    """
```

#### D) Estado de Cuenta
```python
def get_customer_statement(
    partner_code: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> Dict:
    """
    Retorna:
    {
        total_facturado: 10000,
        total_pagado: 6000,
        saldo_adeudado: 4000,
        facturas: [
            { numero, fecha, monto, pagado, saldo, dias_atraso }
        ]
    }
    """
```

### **Esfuerzo:** ~7 horas

---

## 📋 PLAN DE IMPLEMENTACIÓN (En orden de importancia)

### **FASE 1: DEVOLUCIONES (4 horas)**
- Crear tabla `returns` (similar a documents)
- Implementar `post_return()` en inventory.py
- Agregar UI (pestaña "Devoluciones" en main_window.py)
- Registrar en kardex

### **FASE 2: MARGEN (3 horas)**
- Agregar funciones `calculate_cogs()` y `get_product_profitability()`
- Modificar `post_sale()` para incluir margen en respuesta
- Mostrar margen en confirmación de venta
- Agregar columna de margen en kardex

### **FASE 3: DESCUENTOS (6 horas)**
- Crear tabla `customer_discounts`
- Crear tabla `volume_discounts`
- Crear tabla `promotions`
- Modificar UI de venta para aplicar descuentos
- Ajustar cálculo de totales

### **FASE 4: REPORTES (8 horas)**
- Agregar reportes a servicios/reports.py
- Crear nuevas pestañas en main_window.py
- Generar gráficos (ventas, ABC, etc.)
- Exportar a PDF/Excel

### **FASE 5: CRÉDITO (7 horas)**
- Crear tablas de términos de crédito
- Implementar gestión de pagos
- Estado de cuenta por cliente
- Alertas de vencimiento

---

## 🔧 ORDEN RECOMENDADO DE DESARROLLO

1. **DEVOLUCIONES** (PRIMERO) - 4 horas - Funcional básica
2. **MARGEN** (SEGUNDO) - 3 horas - Rápido de implementar, alto impacto
3. **DESCUENTOS** (TERCERO) - 6 horas - Mejora competitividad
4. **CRÉDITO** (CUARTO) - 7 horas - Esencial para B2B
5. **REPORTES** (QUINTO) - 8 horas - Última pieza

**Total: ~28 horas = 3.5 días laborales**

---

## ⚡ ALTERNATIVA: MVP MÍNIMO (1 semana)

Si necesitas vender URGENTE, implementa solo esto:

1. **Devoluciones básicas** (2h) ✅
2. **Mostrar margen en ventas** (1h) ✅
3. **Descuento simple por cliente** (2h) ✅
4. **Reporte simple: Ventas del mes** (2h) ✅
5. **Campo de "términos de pago" en documento** (1h) ✅

**Total:** ~8 horas = 1 día

→ Esto permite vender pero con funciones limitadas

---

## 💾 TABLAS SQL NECESARIAS

```sql
-- DEVOLUCIONES
CREATE TABLE returns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_doc_id INTEGER NOT NULL,
    numero TEXT UNIQUE,
    fecha TEXT,
    motivo TEXT,
    notas TEXT,
    created_at TEXT
);

CREATE TABLE return_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    return_id INTEGER NOT NULL,
    codigo TEXT NOT NULL,
    qty REAL,
    reason TEXT
);

-- DESCUENTOS POR CLIENTE
CREATE TABLE customer_discounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    partner_id INTEGER NOT NULL,
    product_code TEXT,  -- NULL = global para cliente
    discount_percent REAL,
    valid_from TEXT,
    valid_to TEXT
);

-- DESCUENTOS POR VOLUMEN
CREATE TABLE volume_discounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_category TEXT,
    min_qty INTEGER,
    discount_percent REAL
);

-- PROMOCIONES
CREATE TABLE promotions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_code TEXT NOT NULL,
    discount_percent REAL,
    start_date TEXT,
    end_date TEXT,
    max_quantity INTEGER
);

-- PAGOS
CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id INTEGER NOT NULL,
    amount REAL,
    payment_method TEXT,
    payment_date TEXT,
    created_at TEXT
);

-- TÉRMINOS DE CRÉDITO
CREATE TABLE credit_terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    partner_id INTEGER NOT NULL UNIQUE,
    credit_limit REAL,
    payment_terms_days INTEGER DEFAULT 30,
    max_overdue_days INTEGER DEFAULT 60
);
```

---

## 🎬 CONCLUSIÓN

El sistema **ESTÁ BUENO** pero **NO ES VENDIBLE** sin estas funciones críticas.

Recomendamos:
- ✅ **Implementar AHORA:** Devoluciones + Margen + Descuentos (10 horas)
- ✅ **Antes de demostración:** Crédito básico (4 horas)
- ✅ **Después de venta:** Reportes avanzados

Con esto, el sistema será **competitivo con Odoo/SAP básicos**.

---

**Contacto para dudas técnicas sobre implementación:**  
Consultar con equipo de desarrollo sobre timeline.
