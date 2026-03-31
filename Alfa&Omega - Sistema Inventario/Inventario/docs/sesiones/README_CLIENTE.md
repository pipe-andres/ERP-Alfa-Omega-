# 📦 INVENTARIO ALFA & OMEGA — GUÍA DE INSTALACIÓN CLIENTE

**Versión**: 1.0 Premium  
**Fecha**: 26 de enero de 2026  
**Sistema**: Windows 10/11 (x64)  
**Requisitos**: Ninguno especial - es un ejecutable standalone

---

## 🚀 INSTALACIÓN RÁPIDA (3 pasos)

### Paso 1: Descargar
- Descarga el archivo `Inventario_AlfaOmega.zip`
- Guárdalo en una carpeta (ej: `C:\Programas\` o `C:\Users\[TU_USUARIO]\Inventario`)

### Paso 2: Extraer
- Click derecho → "Extraer todo"
- Espera a que se descomprima (~500 MB)

### Paso 3: Ejecutar
- **Doble click** en: `Inventario_AlfaOmega.exe`
- ¡Listo! La app se abre en segundos

---

## 📋 CREDENCIALES DE PRUEBA

**Usuario**: `admin`  
**Contraseña**: `admin123`

(Cambia la contraseña en Parámetros → Usuarios después)

---

## 🎯 PRIMER INICIO

1. **Abre la app**
2. **Login** con las credenciales de prueba
3. **Dashboard**: Verás métricas principales
4. **Inventario**: Prueba agregar un producto
5. **Movimientos**: Registra una compra de prueba

---

## ⚙️ CONFIGURACIÓN INICIAL

### 1. Actualizar datos de la empresa
- Ve a **Parámetros**
- Completa: Nombre, NIT, Dirección, Logo (opcional)
- Click **Guardar**

### 2. Crear usuarios
- Ve a **Usuarios**
- Agregar usuario admin para tu equipo
- Asignar roles (Admin, Operario, etc.)

### 3. Importar datos (si tienes CSV/Excel)
- Ve a **Inventario**
- Click **📥 Importar CSV** o **📥 Importar Excel**
- Selecciona tu archivo

---

## 📊 FUNCIONALIDADES PRINCIPALES

| Sección | Qué hace |
|---------|----------|
| **Dashboard** | Métricas en tiempo real (valor, stock, bajo stock) |
| **Inventario** | Gestión de productos (crear, editar, eliminar, buscar) |
| **Movimientos** | Registrar compras, ventas, ajustes de stock |
| **Reportes** | Kardex (historial de movimientos por producto) |
| **Usuarios** | Crear usuarios, roles, gestionar permisos |
| **Auditoría** | Log de todas las acciones (quién, cuándo, qué) |
| **Parámetros** | Configuración de empresa e impuestos |

---

## 🔒 SEGURIDAD Y DATOS

### Base de datos
- Usa **SQLite** (archivo local: `inventario.db`)
- **Todos los datos quedan en tu computadora**
- No se envían a servidores

### Copias de seguridad
**IMPORTANTE**: Haz backup regularmente
```
1. Cierra la aplicación
2. Copia el archivo: C:\[RUTA_APP]\inventario.db
3. Guárdalo en nube (Google Drive, OneDrive, Dropbox)
```

### Contraseñas
- Encriptadas con bcrypt (seguras)
- Solo el admin puede ver usuarios

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### ❌ "No se puede ejecutar el archivo"
**Solución**: 
- Verifica que descargaste la **versión correcta** (64-bit)
- Prueba: Click derecho → Ejecutar como administrador

### ❌ "Ventana sin contenido"
**Solución**:
- Cierra y abre de nuevo
- Si persiste: elimina archivo `~/.inventario_cache` (si existe)

### ❌ "No puedo logearme"
**Solución**:
- Verifica usuario/contraseña (mayúsculas)
- Usuario por defecto: `admin` / `admin123`
- Cambia contraseña en **Usuarios** después

### ❌ "La app es lenta"
**Solución**:
- Esto es normal la primera vez (inicia BD)
- Las siguientes aperturas son rápidas
- Si persiste, cierra otras aplicaciones

### ❌ "No aparecen mis datos"
**Solución**:
- Verifica que hayas **guardado** (toast verde: ✅)
- Recarga: **F5**
- Revisa Auditoría para confirmar que se registró

---

## 📞 CONTACTO Y SOPORTE

**Por favor reporta**:
- Bugs o comportamientos extraños
- Sugerencias de mejora
- Dificultades en la instalación

**Envía**:
- Descripción del problema
- Screenshot si es posible
- Pasos para reproducir

---

## ✨ CARACTERÍSTICAS PREMIUM (QUE YA TIENEN)

✅ **Diseño Luxury 2026** - Interface premium y moderna  
✅ **Dashboard inteligente** - Métricas en tiempo real  
✅ **Toasts emocionales** - Feedback visual en cada acción  
✅ **Héroes visuales** - Números grandes que dominan  
✅ **Auditoría completa** - Rastro de todos los cambios  
✅ **Multi-usuario** - Sistema de roles y permisos  
✅ **Reportes Kardex** - Historial detallado de movimientos  
✅ **Exportación** - CSV, Excel, PDF  
✅ **Importación** - Carga datos de Excel  
✅ **100% Español** - Interfaz completamente en español  

---

## 🎓 TUTORIAL VIDEO (PENDIENTE)

Mientras tanto:
1. Abre el app
2. Explora cada sección
3. Importa datos de prueba
4. Juega con filtros y búsquedas

---

## 📌 TIPS PRO

### Dashboard
- Los números grandes muestran lo más importante
- Verde = bueno, Rojo = alerta, Azul = información

### Búsqueda inteligente
- Filtra por: Código, Nombre, Categoría
- Busca mientras escribes (sin presionar Enter)

### Exportar
- **CSV**: Para abrir en Excel (editable)
- **Excel**: Para reportes profesionales
- **PDF**: Para imprimir o compartir

### Auditoría
- Revisa quién hizo qué y cuándo
- Filtra por usuario, acción, rango de fechas

---

## 🚀 PRÓXIMAS VERSIONES

Estamos trabajando en:
- [ ] Soporte para PostgreSQL (servidores compartidos)
- [ ] API REST (para integraciones)
- [ ] App móvil (iOS/Android)
- [ ] Sincronización en nube
- [ ] OCR para escanear productos
- [ ] Machine Learning para predicción de stock

---

## 📄 INFORMACIÓN LEGAL

Esta aplicación es **software propietario** de Alfa & Omega.  
Uso únicamente para fines autorizados.

**Versión**: 1.0  
**Licencia**: Comercial  
**Soporte**: 24/5 (respuesta dentro de 24 horas)  

---

## ✅ CHECKLIST PRE-USO

Antes de empezar en producción:

- [ ] App se abre sin errores
- [ ] Puedes loggearte con admin/admin123
- [ ] Puedes crear un usuario nuevo
- [ ] Puedes agregar un producto
- [ ] Puedes registrar una compra/venta
- [ ] Dashboard muestra números actualizados
- [ ] Exportar a Excel funciona
- [ ] Auditoría registra acciones

¿Todo OK? → **¡Listo para usar en producción!**

---

**¡Gracias por confiar en nosotros!**

Alfa & Omega Inventario — Diseñado para vendedores que saben de negocio.

Cualquier pregunta: [correo de soporte]

