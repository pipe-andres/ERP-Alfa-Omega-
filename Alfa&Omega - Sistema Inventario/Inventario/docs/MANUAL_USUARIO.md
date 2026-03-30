# Manual de Usuario — Alfa & Omega ERP
**Sistema de Gestión para Negocios · Versión 3.5**

---

## 1. Primeros Pasos

### Cómo iniciar el sistema
Haz doble clic en el ícono "Alfa & Omega ERP" en tu escritorio.
Ingresa tu usuario y contraseña. El usuario administrador es **admin**.

### Pantalla principal
Al entrar verás el **Dashboard** con:
- 🚨 **Zona de alertas** (arriba): stock crítico y pedidos pendientes
- 📊 **KPIs** (medio): ventas del día, caja, margen, ticket promedio
- 📈 **Gráfico de ventas** con línea de meta
- 🏦 **Inventario resumido** (abajo): valor, stock, compras

### Atajos de teclado
| Tecla | Acción |
|-------|--------|
| F1 | Abrir Punto de Venta |
| F3 | Abrir CRM Clientes |
| F4 | Abrir Control de Caja |
| F5 | Refrescar pantalla |
| F6 | Abrir Reportes |
| F7 | Abrir Órdenes de Compra |
| F8 | Abrir Finanzas |
| F9 | Inteligencia de Negocio |

---

## 2. Inventario

### Agregar un producto
1. Ve a la pestaña **Inventario**
2. Clic en **Nuevo** (o Ctrl+N)
3. Ingresa código, nombre, categoría, precio y cantidad inicial
4. Clic en **Guardar**

### Buscar un producto
Escribe el código o nombre en la barra de búsqueda superior.
Los resultados aparecen al instante.

### Importar productos desde Excel
1. Menú **Inventario → Importar**
2. Selecciona tu archivo Excel (.xlsx)
3. El sistema importa automáticamente código, nombre, precio y cantidad

---

## 3. Punto de Venta (POS)

### Abrir la caja
1. Presiona **F1** o ve a menú **Punto de Venta → Abrir Caja/POS**
2. Ingresa el monto inicial de la caja
3. Clic en **Abrir sesión**

### Registrar una venta
1. Escanea o escribe el código del producto
2. El producto se agrega automáticamente
3. Repite para cada producto
4. Presiona **F12** para cobrar
5. Ingresa el monto recibido → el sistema calcula el cambio
6. Clic en **Cobrar** para finalizar

### Cerrar la caja
1. Presiona **F10** o clic en **Cerrar sesión**
2. Declara el dinero en físico
3. El sistema muestra la diferencia con lo esperado

---

## 4. Clientes (CRM)

### Agregar un cliente
1. Presiona **F3** o menú **Clientes**
2. Clic en **Nuevo cliente**
3. Ingresa nombre, teléfono, email y dirección
4. Clic en **Guardar**

### Ver historial de compras
1. Selecciona el cliente en la lista
2. Ve a la pestaña **Detalle**
3. Verás todas las compras con fechas y montos

### Gestionar crédito
1. Selecciona el cliente
2. Ve a pestaña **Crédito**
3. Ajusta el límite de crédito según tu política

---

## 5. Proveedores y Compras

### Agregar un proveedor
1. Menú **Proveedores**
2. Clic en **Nuevo proveedor**
3. Ingresa nombre, NIT, teléfono y email
4. Clic en **Guardar**

### Crear una orden de compra
1. Presiona **F7** o menú **Compras → Órdenes de Compra**
2. Clic en **Nueva OC**
3. Selecciona el proveedor
4. Agrega los productos y cantidades
5. Clic en **Crear Orden**

### Registrar recepción de mercancía
1. En **Órdenes de Compra** → pestaña **Recepción**
2. Busca el número de la orden
3. Ingresa las cantidades recibidas
4. Clic en **Confirmar Recepción**
5. El stock se actualiza automáticamente

---

## 6. Reportes

### P&L (Pérdidas y Ganancias)
Menú **Reportes → Reportes Avanzados → P&L**
Muestra ventas, costos y margen por período.

### ABC de Productos
Clasifica tus productos en:
- **A**: 80% de tus ingresos (los más importantes)
- **B**: 15% de tus ingresos
- **C**: 5% de tus ingresos (considerar eliminar)

### Exportar reportes
Cada reporte tiene botón **📥 Excel** para descargar en Excel.

---

## 7. Finanzas

### Cuentas por Cobrar (CxC)
Presiona **F8** → pestaña **CxC**
Muestra clientes que te deben dinero con fechas de vencimiento.
- 🔴 Rojo = vencido (cobrar urgente)
- 🟡 Amarillo = por vencer pronto
- 🟢 Verde = al día

### Cuentas por Pagar (CxP)
Pestaña **CxP** — lo que debes a proveedores.

### Flujo de Caja
Pestaña **Flujo** — proyección de entradas y salidas de dinero.

---

## 8. Preguntas Frecuentes

### ¿Cómo hago una devolución?
1. Menú **Punto de Venta → Devoluciones** (o F11)
2. Ingresa el ID de la venta original
3. Selecciona los productos a devolver
4. Ingresa el motivo
5. Clic en **Registrar devolución**

### ¿Cómo cambio la contraseña?
1. Menú **Mi cuenta → Cambiar contraseña**
2. Ingresa la contraseña actual y la nueva
3. Clic en **Guardar**

### ¿Cómo hago un backup?
1. Menú **Archivo → Crear backup**
   O presiona **Ctrl+B**
2. El sistema guarda automáticamente en la carpeta **backups/**
3. También se hace backup automático al cerrar el sistema

### ¿Qué hago si el sistema no abre?
1. Verifica que Python esté instalado
2. Abre la terminal y ejecuta: py main.py
3. Si hay error, contáctanos con el mensaje exacto

### ¿Cómo agrego más usuarios?
1. Ve a la pestaña **Administración**
2. Clic en **Nuevo usuario**
3. Asigna nombre, contraseña y rol (ADMIN/USER/AUDITOR)

---

## Soporte Técnico

📧 **Email:** soporte@alfaomega.co
📱 **WhatsApp:** (indicar número)
🕒 **Horario:** Lunes a Viernes 8am - 6pm (hora Colombia)

---

*Alfa & Omega ERP · Sistema de Gestión Profesional · 2026*
