# 📦 PLAN DISTRIBUCIÓN — CLIENTE PRUEBA DESDE SU PC

**Estado**: Ready to deliver  
**Fecha**: 26 de enero de 2026  
**Cliente**: [Nombre del cliente]

---

## 🎯 OBJETIVO

El cliente necesita **ejecutar la app desde su computadora**, sin dependencias externas.

---

## ✅ SOLUCIÓN ELEGIDA: PORTABLE STANDALONE

### Por qué esta opción:
1. **Cero instalación** — Doble-click y listo
2. **Funciona offline** — Sin necesidad de servidor
3. **Rápido** — Cliente listo en 3 minutos
4. **Seguro** — Datos locales, sin cloud
5. **Versátil** — Fácil iterar si hay cambios

---

## 📋 QUÉ INCLUIR EN EL PAQUETE

```
Inventario_v1.0/
├── main.py                    (app principal)
├── inventario.db              (BD SQLite lista para usar)
├── run.bat                    (script para ejecutar)
├── README_CLIENTE.md          (instrucciones)
├── src/                       (todo el código)
│   ├── app/
│   ├── services/
│   ├── core/
│   └── database/
├── assets/                    (imagenes, logos, etc)
└── .venv/                     (Python + dependencias precompiladas)
```

**Tamaño total**: ~600-700 MB

---

## 🚀 PASOS PARA PREPARAR

### 1️⃣ Crear la carpeta distributable
```bash
cd C:\ruta\al\proyecto
mkdir Inventario_v1.0
```

### 2️⃣ Copiar archivos
```bash
# Copiar core
cp main.py Inventario_v1.0/
cp inventario.db Inventario_v1.0/
cp README_CLIENTE.md Inventario_v1.0/
cp requirements.txt Inventario_v1.0/

# Copiar directorios
cp -r src Inventario_v1.0/
cp -r assets Inventario_v1.0/
cp -r .venv Inventario_v1.0/
```

### 3️⃣ Crear `run.bat`
```batch
@echo off
REM Inventario Alfa & Omega v1.0
cd /d "%~dp0"
.venv\Scripts\python.exe main.py
pause
```

### 4️⃣ Empaquetar en ZIP
```bash
# Opción A: Windows (7-Zip)
# Click derecho en carpeta → 7-Zip → Comprimir

# Opción B: Simplemente compartir la carpeta
# Por Google Drive, OneDrive, etc.
```

---

## 📤 ENTREGAR AL CLIENTE

### Opción A: Google Drive/OneDrive
1. Cargar carpeta `Inventario_v1.0` completa
2. Compartir link
3. Cliente descarga y extrae

### Opción B: ZIP comprimido
1. Crear ZIP (~600-700 MB)
2. Puede enviarse por email o file transfer service
3. Cliente extrae

### Opción C: Nube compartida
1. Subirá a Dropbox/Drive
2. Cliente accede directamente

---

## 📥 CLIENTE INSTALA (3 PASOS)

### Paso 1: Descargar
- Cliente descarga `Inventario_v1.0.zip` o accede a drive

### Paso 2: Extraer
- Click derecho → "Extraer aquí"
- O arrastra carpeta a donde quiera (C:\Programas\, Desktop, etc.)

### Paso 3: Ejecutar
- **Doble-click en `run.bat`**
- Espera 10 segundos
- App se abre

### Paso 4: Login
- Usuario: `admin`
- Contraseña: `admin123`

---

## ✨ VENTAJAS PARA CLIENTE

| Aspecto | Beneficio |
|---------|-----------|
| **Setup** | Ninguno — funciona inmediatamente |
| **Datos** | Todo local — privado |
| **Offline** | Funciona sin internet |
| **Desinstalar** | Solo borrar carpeta |
| **Actualizar** | Descargar nueva versión |
| **Portátil** | Llevar en USB si quiere |

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### ❌ "No se puede ejecutar run.bat"
**Solución**: 
- Click derecho → "Ejecutar como administrador"
- O copiar ruta exacta en terminal

### ❌ "App abre pero sin contenido"
**Solución**:
- Espera 10 segundos más (primera carga)
- Cierra y abre de nuevo

### ❌ "Falta archivo .venv"
**Solución**:
- Verifica que descargaste carpeta **completa**
- Si falta: cliente debe instalar Python y ejecutar `pip install -r requirements.txt`

### ❌ "SQL error: database is locked"
**Solución**:
- Cierra app completamente
- Elimina cualquier archivo `.lock` en carpeta
- Abre de nuevo

---

## 📊 CHECKLIST PRE-ENVÍO

- [ ] Carpeta `Inventario_v1.0` creada
- [ ] `main.py` presente
- [ ] `inventario.db` presente (BD inicializada)
- [ ] `src/` completo
- [ ] `assets/` presente
- [ ] `.venv/` presente con todas las dependencias
- [ ] `run.bat` creado
- [ ] `README_CLIENTE.md` incluido
- [ ] Tests 28/28 pasando ✅
- [ ] App se abre sin errores
- [ ] Login funciona (admin/admin123)
- [ ] Puedo agregar producto
- [ ] Puedo registrar movimiento
- [ ] Dashboard muestra datos

**Si todo ✅**: LISTO PARA ENVIAR

---

## 🎁 BONUS: CREAR ACCESO DIRECTO

Cliente puede crear acceso directo en Desktop:

1. En `Inventario_v1.0`, doble-click en `run.bat`
2. Crear acceso directo en Desktop
3. Renombrar: `Inventario Alfa & Omega`
4. Listo — ejecuta desde Desktop

---

## ⏱️ TIMELINE

| Paso | Tiempo |
|------|--------|
| Copiar archivos | 2 min |
| Crear run.bat | 1 min |
| Comprimir ZIP | 3 min |
| **Total** | **~6 minutos** |

---

## 🔐 CONSIDERACIONES SEGURIDAD

- ✅ BD SQLite local — datos privados
- ✅ Sin envíos a servidor
- ✅ Contraseñas encriptadas (bcrypt)
- ✅ Logs de auditoría incluidos

**Recomendación**: Cliente haga backup regularmente de `inventario.db`

---

## 📞 SOPORTE CLIENTE

Si cliente tiene problemas:
1. Compartir screenshot del error
2. Describir qué pasó
3. Enviar archivo `inventario.db` (si aplica)

Nosotros: respuesta 24h

---

## 🚀 PRÓXIMO PASO

¿Ejecutamos `prepare_distribution.bat`?

Si SÍ:
1. Abre terminal en proyecto
2. Ejecuta: `.\prepare_distribution.bat`
3. Carpeta `Inventario_v1.0` lista
4. Comprimir y enviar

---

**Estado**: 🟢 LISTO PARA ENTREGAR

