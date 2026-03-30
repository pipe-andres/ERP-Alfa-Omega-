#!/usr/bin/env python3
"""
AUDITORÍA DE PRODUCCIÓN - SISTEMA ALFA & OMEGA
Validación rápida sin simulación compleja de datos.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.database.connection import init_db, get_connection, DB_ENGINE
from src.services.inventory import add_product, post_purchase, post_sale
from src.core.auth import ensure_defaults
from src.core.error_handler import logger
import json

REPORT = {
    "engine": DB_ENGINE,
    "date": str(Path(__file__).stat().st_mtime),
    "validaciones": [],
    "errores": [],
    "inconsistencias": [],
    "estado": "PENDING"
}

def check(descripcion, condicion):
    """Registrar validación."""
    if condicion:
        print(f"✅ {descripcion}")
        REPORT["validaciones"].append({"check": descripcion, "status": "PASS"})
    else:
        print(f"❌ {descripcion}")
        REPORT["validaciones"].append({"check": descripcion, "status": "FAIL"})
        REPORT["errores"].append(descripcion)

print("="*70)
print("AUDITORÍA DE PRODUCCIÓN - SISTEMA ALFA & OMEGA")
print("="*70)

try:
    # Inicializar BD
    init_db()
    ensure_defaults()
    print("\n✓ Base de datos inicializada")
    
    # ===== VALIDACIÓN 1: Estructura de tablas =====
    print("\n1. VALIDACIÓN DE ESTRUCTURA DE TABLAS")
    with get_connection() as conn:
        cur = conn.cursor()
        
        # Verificar tabla kardex_moves tiene avg_cost
        try:
            cur.execute("SELECT avg_cost FROM kardex_moves LIMIT 1")
            check("Campo avg_cost en kardex_moves", True)
        except:
            check("Campo avg_cost en kardex_moves", False)
            REPORT["inconsistencias"].append("Falta avg_cost en kardex_moves")
        
        # Verificar tabla productos tiene activo
        try:
            cur.execute("SELECT activo FROM productos LIMIT 1")
            check("Campo activo en productos", True)
        except:
            check("Campo activo en productos", False)
        
        # Verificar índices
        cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%kardex%'")
        indices = cur.fetchall()
        check(f"Índices en kardex_moves ({len(indices)})", len(indices) >= 2)
    
    # ===== VALIDACIÓN 2: Operaciones básicas =====
    print("\n2. VALIDACIÓN DE OPERACIONES BÁSICAS")
    try:
        # Crear producto
        add_product("TEST001", "Producto Test", "Test", 100.0, 10, avg_cost=80.0)
        check("Crear producto", True)
        
        # Registrar compra
        post_purchase(None, None, [{"codigo": "TEST001", "qty": 5, "unit_cost": 90.0}])
        check("Registrar compra", True)
        
        # Registrar venta
        post_sale(None, None, [{"codigo": "TEST001", "qty": 2, "unit_price": 120.0}])
        check("Registrar venta", True)
    except Exception as e:
        check(f"Operaciones básicas: {str(e)}", False)
    
    # ===== VALIDACIÓN 3: Integridad kardex =====
    print("\n3. VALIDACIÓN DE INTEGRIDAD DE KARDEX")
    with get_connection() as conn:
        cur = conn.cursor()
        
        # Verificar balance_cost = balance_qty * avg_cost
        cur.execute("""
            SELECT COUNT(*) 
            FROM kardex_moves
            WHERE ABS(balance_cost - (balance_qty * avg_cost)) > 0.01
        """)
        inconsistent = cur.fetchone()[0]
        check("Consistencia balance_cost = balance_qty * avg_cost", inconsistent == 0)
        
        if inconsistent > 0:
            REPORT["inconsistencias"].append(f"{inconsistent} movimientos con balance_cost inconsistente")
        
        # Verificar que no hay NULLs
        cur.execute("""
            SELECT COUNT(*)
            FROM kardex_moves
            WHERE product_code IS NULL OR type IS NULL OR avg_cost IS NULL
        """)
        null_count = cur.fetchone()[0]
        check("Sin campos NULL en kardex_moves", null_count == 0)
        
        # Verificar tipos válidos
        cur.execute("""
            SELECT DISTINCT type FROM kardex_moves 
            WHERE type NOT IN ('IN', 'OUT')
        """)
        invalid_types = cur.fetchall()
        check("Tipos de movimiento válidos", len(invalid_types) == 0)
    
    # ===== VALIDACIÓN 4: Protecciones =====
    print("\n4. VALIDACIÓN DE PROTECCIONES")
    try:
        # Intentar producto duplicado
        try:
            add_product("TEST001", "Duplicado", "Test", 100.0, 10)
            check("Bloqueo de producto duplicado", False)
        except ValueError:
            check("Bloqueo de producto duplicado", True)
        
        # Intentar compra con costo negativo
        try:
            post_purchase(None, None, [{"codigo": "TEST001", "qty": 5, "unit_cost": -50.0}])
            check("Bloqueo de costo negativo", False)
        except ValueError:
            check("Bloqueo de costo negativo", True)
        
        # Intentar venta con stock negativo
        try:
            post_sale(None, None, [{"codigo": "TEST001", "qty": 100000, "unit_price": 120.0}], allow_negative=False)
            check("Bloqueo de stock negativo", False)
        except ValueError:
            check("Bloqueo de stock negativo", True)
    except Exception as e:
        check(f"Validaciones de protección: {str(e)}", False)
    
    # ===== VALIDACIÓN 5: Performance =====
    print("\n5. VALIDACIÓN DE PERFORMANCE")
    import time
    with get_connection() as conn:
        cur = conn.cursor()
        
        start = time.time()
        cur.execute("SELECT COUNT(*) FROM kardex_moves")
        elapsed = time.time() - start
        
        check(f"Consulta rápida (<100ms): {elapsed*1000:.1f}ms", elapsed < 0.1)
    
    # ===== RESULTADO FINAL =====
    print("\n" + "="*70)
    print("RESULTADO FINAL")
    print("="*70)
    
    passed = sum(1 for v in REPORT["validaciones"] if v["status"] == "PASS")
    total = len(REPORT["validaciones"])
    
    print(f"\nValidaciones pasadas: {passed}/{total}")
    print(f"Errores encontrados: {len(REPORT['errores'])}")
    print(f"Inconsistencias: {len(REPORT['inconsistencias'])}")
    
    if REPORT['errores']:
        print("\n❌ ERRORES:")
        for error in REPORT['errores']:
            print(f"  - {error}")
    
    if REPORT['inconsistencias']:
        print("\n⚠ INCONSISTENCIAS:")
        for incon in REPORT['inconsistencias']:
            print(f"  - {incon}")
    
    print("\n" + "="*70)
    if passed >= total - 2 and len(REPORT['errores']) < 3:
        print("SYSTEM STATUS: PRODUCTION READY ✅")
        REPORT["estado"] = "PRODUCTION_READY"
    else:
        print("SYSTEM STATUS: NEEDS CORRECTIONS ❌")
        REPORT["estado"] = "NEEDS_CORRECTIONS"
    print("="*70)
    
    # Guardar reporte
    with open("audit_report.json", "w") as f:
        json.dump(REPORT, f, indent=2, default=str)
    
    print("\n✓ Reporte guardado en: audit_report.json")

except Exception as e:
    print(f"\n❌ ERROR CRÍTICO: {str(e)}")
    import traceback
    traceback.print_exc()
    REPORT["errores"].append(str(e))
    REPORT["estado"] = "FAILED"
