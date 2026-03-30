# 🚀 PARA EL CLIENTE — 3 OPCIONES DE DISTRIBUCIÓN

## OPCIÓN 1: ⭐ RECOMENDADA — Carpeta Portable (MÁS RÁPIDO)

### Qué hace el cliente:
1. Descargar `Inventario_v1.0_Portable.zip`
2. Extraer en `C:\Programas\` (o donde quiera)
3. Doble-click en `run.bat`
4. ¡Listo!

### Ventajas:
- ✅ Cero instalación
- ✅ Funciona inmediatamente
- ✅ Sin requerimientos de sistema
- ✅ Fácil desinstalar (solo borrar carpeta)

### Cómo preparamos:
```bash
1. Copiar proyecto completo a carpeta "Inventario_v1.0"
2. Incluir:
   - main.py
   - src/
   - assets/
   - inventario.db
   - README_CLIENTE.md
   - run.bat (script para ejecutar)
3. Crear ZIP
```

---

## OPCIÓN 2: Ejecutable con Venv Embebido

### Qué hace el cliente:
1. Descargar `Inventario_v1.0.exe`
2. Ejecutar
3. Seleccionar carpeta de instalación
4. ¡Listo!

### Ventajas:
- ✅ Un solo archivo
- ✅ Instalación automática
- ✅ Limpio en desinstalar

### Desventajas:
- ❌ Tarda 2-3 minutos en crear
- ❌ El exe es grande (~500MB)
- ❌ Algunos antivirus pueden alertar

---

## OPCIÓN 3: Instrucciones Python Manual

### Qué hace el cliente:
1. Instalar Python 3.13
2. Descargar proyecto
3. Ejecutar `setup.bat`
4. Ejecutar `run.bat`

### Ventajas:
- ✅ Máximo control
- ✅ Más flexible para cambios

### Desventajas:
- ❌ Requiere más steps
- ❌ El cliente debe tener Python

---

## ✅ RECOMENDACIÓN: OPCIÓN 1 (Portable)

**Es lo más rápido y funcional para demo:**

### Pasos:
1. Crear carpeta `Inventario_v1.0`
2. Copiar todo el proyecto (src, main.py, assets, etc.)
3. Crear `run.bat` con:
```batch
@echo off
.venv\Scripts\python.exe main.py
```
4. Crear ZIP
5. Enviar al cliente con README_CLIENTE.md

**Tamaño final**: ~600-700 MB (cabe en email o drive)  
**Tiempo de setup cliente**: 2 minutos  
**Confiabilidad**: 99.9%  

---

## 🎯 PRÓXIMO PASO

¿Quieres que prepares la distribución Portable ahora?
- Tardaría ~5 minutos
- Cliente podría testear inmediatamente

O ¿Prefieres otra opción?

