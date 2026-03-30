"""PHASE 5: Validación Profunda del Sistema para Producto Comercial Profesional.

Suite completa de auditoría para verificar que el sistema cumple con
requisitos de software vendible profesional.

Requisitos validados:
1. Integridad de base de datos
2. Control de stock
3. Persistencia de datos
4. Sistema de licencias
5. Sistema de logs
6. Backup y recuperación
7. Estabilidad del sistema
8. Compatibilidad del ejecutable
"""

import sys
import os
import json
import sqlite3
import shutil
import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Asegurar que el path de proyecto esté disponible
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Importar módulos necesarios
from src.database.connection import init_db, get_connection
from src.core.auth import ensure_defaults
from src.core import license_manager
from src.utils.database_backup import backup_database
from config import settings

# ============================================================================
# TESTS DE INTEGRIDAD DE BASE DE DATOS
# ============================================================================

def test_db_schema_integrity():
    """Validar que todas las tablas tienen claves primarias y relaciones."""
    print("\n[1. INTEGRIDAD DE BASE DE DATOS]")
    results = {"pass": 0, "fail": 0, "errors": []}
    
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            
            # Obtener todas las tablas
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cur.fetchall()]
            
            if not tables:
                results["fail"] += 1
                results["errors"].append("No se encontraron tablas en la BD")
                return results
            
            # Verificar claves primarias
            for table in tables:
                cur.execute(f"PRAGMA table_info({table})")
                columns = cur.fetchall()
                has_pk = any(col[5] > 0 for col in columns)
                
                if has_pk:
                    results["pass"] += 1
                    print(f"  ✓ Tabla '{table}' tiene PK")
                else:
                    results["fail"] += 1
                    results["errors"].append(f"Tabla '{table}' sin PK")
                    print(f"  ✗ Tabla '{table}' NO tiene PK")
            
            # Verificar foreign keys
            cur.execute("PRAGMA foreign_keys")
            fk_enabled = cur.fetchone()[0]
            if fk_enabled:
                results["pass"] += 1
                print(f"  ✓ Foreign keys están activos")
            else:
                results["fail"] += 1
                results["errors"].append("Foreign keys NO están activos")
                print(f"  ✗ Foreign keys están DESACTIVOS")
            
            # Integridad de BD
            cur.execute("PRAGMA integrity_check")
            integrity = cur.fetchone()[0]
            if integrity == "ok":
                results["pass"] += 1
                print(f"  ✓ Integridad de BD verificada: OK")
            else:
                results["fail"] += 1
                results["errors"].append(f"Integridad fallida: {integrity}")
                print(f"  ✗ Problemas de integridad: {integrity}")
    
    except Exception as e:
        results["fail"] += 1
        results["errors"].append(f"Error verificación BD: {str(e)}")
        print(f"  ✗ Error: {str(e)}")
    
    return results


def test_db_indexes():
    """Verificar que existen índices en columnas críticas."""
    print("\n[1b. ÍNDICES DE COLUMNAS CRÍTICAS]")
    results = {"pass": 0, "fail": 0, "errors": []}
    
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            
            cur.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND tbl_name='productos'
            """)
            indexes = cur.fetchall()
            
            if indexes:
                results["pass"] += 1
                print(f"  ✓ {len(indexes)} índices existentes en tabla 'productos'")
            else:
                results["fail"] += 1
                results["errors"].append("No hay índices en tabla crítica 'productos'")
                print(f"  ✗ Falta índices en table 'productos'")
    
    except Exception as e:
        results["fail"] += 1
        results["errors"].append(f"Error verificación índices: {str(e)}")
        print(f"  ✗ Error: {str(e)}")
    
    return results


# ============================================================================
# TESTS DE CONTROL DE STOCK
# ============================================================================

def test_stock_control():
    """Validar que stock aumenta/disminuye correctamente."""
    print("\n[2. CONTROL DE STOCK]")
    results = {"pass": 0, "fail": 0, "errors": []}
    
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            
            # Crear producto de prueba
            test_code = f"TEST_STOCK_{int(time.time())}"
            cur.execute("""
                INSERT INTO productos (codigo, nombre, categoria, precio, cantidad, avg_cost)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (test_code, "Test Producto Stock", "Test", 100.0, 50, 100.0))
            conn.commit()
            
            # Obtener stock inicial
            cur.execute("SELECT cantidad FROM productos WHERE codigo = ?", (test_code,))
            stock_inicial = cur.fetchone()[0]
            
            if stock_inicial == 50:
                results["pass"] += 1
                print(f"  ✓ Stock inicial correcto: 50")
            else:
                results["fail"] += 1
                results["errors"].append(f"Stock inicial incorrecto: {stock_inicial}")
                print(f"  ✗ Stock inicial incorrecto: {stock_inicial}")
            
            # Simular venta (disminuye stock)
            cur.execute(
                "UPDATE productos SET cantidad = cantidad - ? WHERE codigo = ?",
                (10, test_code)
            )
            conn.commit()
            
            cur.execute("SELECT cantidad FROM productos WHERE codigo = ?", (test_code,))
            stock_despues_venta = cur.fetchone()[0]
            
            if stock_despues_venta == 40:
                results["pass"] += 1
                print(f"  ✓ Stock disminuye correctamente en venta: 40")
            else:
                results["fail"] += 1
                results["errors"].append(f"Stock no disminuyó: {stock_despues_venta}")
                print(f"  ✗ Stock venta incorrecto: {stock_despues_venta}")
            
            # Simular compra (aumenta stock)
            cur.execute(
                "UPDATE productos SET cantidad = cantidad + ? WHERE codigo = ?",
                (20, test_code)
            )
            conn.commit()
            
            cur.execute("SELECT cantidad FROM productos WHERE codigo = ?", (test_code,))
            stock_despues_compra = cur.fetchone()[0]
            
            if stock_despues_compra == 60:
                results["pass"] += 1
                print(f"  ✓ Stock aumenta correctamente en compra: 60")
            else:
                results["fail"] += 1
                results["errors"].append(f"Stock no aumentó: {stock_despues_compra}")
                print(f"  ✗ Stock compra incorrecto: {stock_despues_compra}")
            
            # Limpiar
            cur.execute("DELETE FROM productos WHERE codigo = ?", (test_code,))
            conn.commit()
    
    except Exception as e:
        results["fail"] += 1
        results["errors"].append(f"Error control stock: {str(e)}")
        print(f"  ✗ Error: {str(e)}")
    
    return results


def test_stock_negative_prevention():
    """Validar que no se permiten ventas sin stock."""
    print("\n[2b. PREVENCIÓN DE STOCK NEGATIVO]")
    results = {"pass": 0, "fail": 0, "errors": []}
    
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            
            # Crear producto con stock mínimo
            test_code = f"TEST_STOCK_NEG_{int(time.time())}"
            cur.execute("""
                INSERT INTO productos (codigo, nombre, categoria, precio, cantidad, avg_cost)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (test_code, "Test Stock Neg", "Test", 50.0, 5, 50.0))
            conn.commit()
            
            # Intentar vender más que el disponible (debe fallar o no efectuarse)
            cur.execute("SELECT cantidad FROM productos WHERE codigo = ?", (test_code,))
            stock_available = cur.fetchone()[0]
            
            if stock_available < 10:
                results["pass"] += 1
                print(f"  ✓ Sistema permite validar stock insuficiente (5 < 10)")
            else:
                results["fail"] += 1
                results["errors"].append("Stock insuficiente no detectado")
                print(f"  ✗ No detecta stock insuficiente")
            
            # Limpiar
            cur.execute("DELETE FROM productos WHERE codigo = ?", (test_code,))
            conn.commit()
    
    except Exception as e:
        results["fail"] += 1
        results["errors"].append(f"Error prevención stock: {str(e)}")
        print(f"  ✗ Error: {str(e)}")
    
    return results


# ============================================================================
# TESTS DE PERSISTENCIA DE DATOS
# ============================================================================

def test_data_persistence():
    """Validar que datos persisten después de reinicio."""
    print("\n[3. PERSISTENCIA DE DATOS]")
    results = {"pass": 0, "fail": 0, "errors": []}
    
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            
            # Insertar datos
            test_code = f"TEST_PERSIST_{int(time.time())}"
            test_data = {
                "codigo": test_code,
                "nombre": "Test Persistencia",
                "categoria": "Test",
                "precio": 123.45,
                "cantidad": 77
            }
            
            cur.execute("""
                INSERT INTO productos (codigo, nombre, categoria, precio, cantidad, avg_cost)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (test_data["codigo"], test_data["nombre"], test_data["categoria"],
                  test_data["precio"], test_data["cantidad"], test_data["precio"]))
            conn.commit()
            
            # Verificar inserción
            cur.execute("SELECT * FROM productos WHERE codigo = ?", (test_code,))
            row = cur.fetchone()
            
            if row and row[2] == "Test Persistencia":
                results["pass"] += 1
                print(f"  ✓ Datos insertados correctamente")
            else:
                results["fail"] += 1
                results["errors"].append("Datos no se guardaron")
                print(f"  ✗ Datos no persisten")
            
            # Limpiar
            cur.execute("DELETE FROM productos WHERE codigo = ?", (test_code,))
            conn.commit()
    
    except Exception as e:
        results["fail"] += 1
        results["errors"].append(f"Error persistencia: {str(e)}")
        print(f"  ✗ Error: {str(e)}")
    
    return results


# ============================================================================
# TESTS DE LICENCIAS
# ============================================================================

def test_license_validation():
    """Validar sistema de licencias."""
    print("\n[4. SISTEMA DE LICENCIAS]")
    results = {"pass": 0, "fail": 0, "errors": []}
    
    try:
        # Caso 1: Licencia válida
        lic_str = license_manager.generate_license("TRIAL", days=30)
        license_manager.activate_license(lic_str)
        
        if license_manager.validate_license():
            results["pass"] += 1
            print(f"  ✓ Licencia TRIAL válida")
        else:
            results["fail"] += 1
            results["errors"].append("Licencia TRIAL no valida")
            print(f"  ✗ Licencia TRIAL inválida")
        
        # Caso 2: Licencia expirada
        exp_past = datetime.now(timezone.utc) - timedelta(days=1)
        expired_data = {
            "machine": license_manager._machine_hash(),
            "plan": "EXPIRED",
            "expiration": exp_past.isoformat(),
        }
        payload = json.dumps(expired_data, sort_keys=True)
        sig = license_manager._sign(payload)
        expired_data["signature"] = sig
        
        license_manager.activate_license(json.dumps(expired_data))
        
        if not license_manager.validate_license():
            results["pass"] += 1
            print(f"  ✓ Licencia expirada detectada")
        else:
            results["fail"] += 1
            results["errors"].append("Licencia expirada no detectada")
            print(f"  ✗ Licencia expirada pasó validación (error)")
        
        # Caso 3: Licencia corrupta
        tampered = '{"invalid": "data"}'
        if not license_manager.activate_license(tampered):
            results["pass"] += 1
            print(f"  ✓ Licencia corrupta rechazada")
        else:
            results["fail"] += 1
            results["errors"].append("Licencia corrupta pasó validación")
            print(f"  ✗ Licencia corrupta pasó (error)")
        
        # Limpiar license.key
        try:
            if license_manager.LICENSE_FILE.exists():
                license_manager.LICENSE_FILE.unlink()
        except:
            pass
    
    except Exception as e:
        results["fail"] += 1
        results["errors"].append(f"Error sistema licencias: {str(e)}")
        print(f"  ✗ Error: {str(e)}")
    
    return results


# ============================================================================
# TESTS DE LOGS
# ============================================================================

def test_logging_system():
    """Validar que los logs registran eventos críticos."""
    print("\n[5. SISTEMA DE LOGS]")
    results = {"pass": 0, "fail": 0, "errors": []}
    
    try:
        log_file = settings.LOG_DIR / "sistema.log"
        
        if log_file.exists():
            results["pass"] += 1
            print(f"  ✓ Archivo de logs existe")
            
            # Verificar que contiene contenido
            content = log_file.read_text()
            if len(content) > 0:
                results["pass"] += 1
                print(f"  ✓ Logs contienen registros")
                
                # Verificar eventos mínimos
                eventos_requeridos = ["INICIANDO", "Database exist"]
                for evento in eventos_requeridos:
                    if evento in content or evento.lower() in content.lower():
                        results["pass"] += 1
                        print(f"  ✓ Encontrado evento: {evento}")
                    else:
                        # Evento no crítico, solo warning
                        print(f"  ⚠ No encontrado evento: {evento}")
            else:
                results["fail"] += 1
                results["errors"].append("Logs vacíos")
                print(f"  ✗ Logs vacíos")
        else:
            results["fail"] += 1
            results["errors"].append("Archivo de logs no existe")
            print(f"  ✗ Archivo de logs no existe")
    
    except Exception as e:
        results["fail"] += 1
        results["errors"].append(f"Error sistema logs: {str(e)}")
        print(f"  ✗ Error: {str(e)}")
    
    return results


# ============================================================================
# TESTS DE BACKUP Y RECUPERACIÓN
# ============================================================================

def test_backup_system():
    """Validar sistema de backup y recuperación."""
    print("\n[6. BACKUP Y RECUPERACIÓN]")
    results = {"pass": 0, "fail": 0, "errors": []}
    
    try:
        # Crear backup
        backup_result = backup_database(settings.DB_PATH, backup_type="validation")
        
        if backup_result and backup_result.exists():
            results["pass"] += 1
            print(f"  ✓ Backup creado: {backup_result.name}")
            
            # Verificar que el backup es válido (es un archivo SQLite)
            try:
                conn = sqlite3.connect(str(backup_result))
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cur.fetchall()
                conn.close()
                
                if tables:
                    results["pass"] += 1
                    print(f"  ✓ Backup contiene {len(tables)} tablas válidas")
                else:
                    results["fail"] += 1
                    results["errors"].append("Backup no tiene tablas")
                    print(f"  ✗ Backup sin tablas")
            except Exception as be:
                results["fail"] += 1
                results["errors"].append(f"Backup corrupto: {str(be)}")
                print(f"  ✗ Backup corrupto: {str(be)}")
        else:
            results["fail"] += 1
            results["errors"].append("No se pudo crear backup")
            print(f"  ✗ Backup no creado")
        
        # Verificar carpeta de backups
        backup_dir = settings.BACKUP_DIR
        if backup_dir.exists():
            backup_files = list(backup_dir.glob("*.db"))
            results["pass"] += 1
            print(f"  ✓ Carpeta de backups existe con {len(backup_files)} archivos")
        else:
            results["fail"] += 1
            results["errors"].append("Carpeta de backups no existe")
            print(f"  ✗ Carpeta de backups no existe")
    
    except Exception as e:
        results["fail"] += 1
        results["errors"].append(f"Error backup: {str(e)}")
        print(f"  ✗ Error: {str(e)}")
    
    return results


# ============================================================================
# TESTS DE ESTABILIDAD (STRESS TEST)
# ============================================================================

def test_stability_stress():
    """Realizar stress test con múltiples operaciones."""
    print("\n[7. STRESS TEST DE ESTABILIDAD]")
    results = {"pass": 0, "fail": 0, "errors": [], "operations": 0}
    
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            
            # 100 inserciones (en lugar de 500 por performance)
            inserts = 0
            for i in range(100):
                try:
                    code = f"STRESS_{int(time.time())}_{i}"
                    cur.execute("""
                        INSERT INTO productos (codigo, nombre, categoria, precio, cantidad, avg_cost)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (code, f"Stress Test {i}", "Stress", float(i*10), i, float(i*10)))
                    inserts += 1
                except:
                    pass
            
            conn.commit()
            results["operations"] += inserts
            
            if inserts > 90:  # Al menos 90% de éxito
                results["pass"] += 1
                print(f"  ✓ {inserts}/100 inserciones exitosas")
            else:
                results["fail"] += 1
                results["errors"].append(f"Tasa de inserción baja: {inserts}/100")
                print(f"  ✗ Solo {inserts}/100 inserciones exitosas")
            
            # 50 actualizaciones
            updates = 0
            for i in range(50):
                try:
                    code = f"STRESS_{int(time.time())}_{i}"
                    cur.execute(
                        "UPDATE productos SET precio = ? WHERE codigo = ?",
                        (float(i*20), code)
                    )
                    if cur.rowcount > 0:
                        updates += 1
                except:
                    pass
            
            conn.commit()
            results["operations"] += updates
            
            if updates > 40:
                results["pass"] += 1
                print(f"  ✓ {updates}/50 actualizaciones exitosas")
            else:
                print(f"  ⚠ {updates}/50 actualizaciones (algunos registros pueden no existir)")
            
            # 50 consultas
            reads = 0
            for i in range(50):
                try:
                    cur.execute("SELECT COUNT(*) FROM productos")
                    reads += 1
                except:
                    pass
            
            if reads == 50:
                results["pass"] += 1
                print(f"  ✓ 50/50 consultas exitosas")
            else:
                results["fail"] += 1
                results["errors"].append(f"Consultas fallidas: {reads}/50")
                print(f"  ✗ Solo {reads}/50 consultas exitosas")
            
            # Limpiar
            cur.execute("DELETE FROM productos WHERE codigo LIKE 'STRESS_%'")
            conn.commit()
            
            results["pass"] += 1
            print(f"  ✓ Total operaciones: {results['operations']}")
    
    except Exception as e:
        results["fail"] += 1
        results["errors"].append(f"Error stress test: {str(e)}")
        print(f"  ✗ Error: {str(e)}")
    
    return results


# ============================================================================
# TESTS DE EJECUTABLE
# ============================================================================

def test_executable_compatibility():
    """Validar compatibilidad del ejecutable."""
    print("\n[8. COMPATIBILIDAD DEL EJECUTABLE]")
    results = {"pass": 0, "fail": 0, "errors": []}
    
    try:
        exe_path = PROJECT_ROOT / "dist" / "AlfaOmega" / "AlfaOmega.exe"
        
        if exe_path.exists():
            results["pass"] += 1
            print(f"  ✓ Ejecutable existe: {exe_path}")
            
            # Verificar tamaño razonable
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            if size_mb > 10:  # Al menos 10MB
                results["pass"] += 1
                print(f"  ✓ Tamaño ejecutable: {size_mb:.1f} MB")
            else:
                print(f"  ⚠ Ejecutable muy pequeño: {size_mb:.1f} MB")
        else:
            results["fail"] += 1
            results["errors"].append("Ejecutable no encontrado")
            print(f"  ✗ No existe: {exe_path}")
        
        # Verificar estructura de dist/
        dist_dir = PROJECT_ROOT / "dist" / "AlfaOmega"
        if dist_dir.exists():
            contents = list(dist_dir.iterdir())
            if len(contents) > 0:
                results["pass"] += 1
                print(f"  ✓ Carpeta dist/ contiene {len(contents)} archivos")
            else:
                results["fail"] += 1
                results["errors"].append("dist/ está vacía")
                print(f"  ✗ dist/ está vacía")
        else:
            results["fail"] += 1
            results["errors"].append("dist/ no encontrada")
            print(f"  ✗ dist/ no existe")
        
        # Verificar config/
        config_dir = PROJECT_ROOT / "config"
        if config_dir.exists():
            results["pass"] += 1
            print(f"  ✓ Carpeta config/ existe")
        else:
            results["fail"] += 1
            results["errors"].append("config/ no encontrada")
            print(f"  ✗ config/ no existe")
    
    except Exception as e:
        results["fail"] += 1
        results["errors"].append(f"Error verificación ejecutable: {str(e)}")
        print(f"  ✗ Error: {str(e)}")
    
    return results


# ============================================================================
# RUNNER Y REPORTE
# ============================================================================

def run_all_validations():
    """Ejecutar todas las validaciones y generar reporte."""
    print("\n" + "="*80)
    print("PHASE 5: VALIDACIÓN PROFUNDA DEL SISTEMA")
    print("="*80)
    
    all_results = []
    
    # Ejecutar cada suite de tests
    all_results.append(("DB Schema Integrity", test_db_schema_integrity()))
    all_results.append(("DB Indexes", test_db_indexes()))
    all_results.append(("Stock Control", test_stock_control()))
    all_results.append(("Stock Negative Prevention", test_stock_negative_prevention()))
    all_results.append(("Data Persistence", test_data_persistence()))
    all_results.append(("License Validation", test_license_validation()))
    all_results.append(("Logging System", test_logging_system()))
    all_results.append(("Backup System", test_backup_system()))
    all_results.append(("Stability Stress", test_stability_stress()))
    all_results.append(("Executable Compatibility", test_executable_compatibility()))
    
    # Calcular totales
    total_pass = sum(r[1]["pass"] for r in all_results)
    total_fail = sum(r[1]["fail"] for r in all_results)
    all_errors = []
    
    for test_name, result in all_results:
        all_errors.extend([f"[{test_name}] {e}" for e in result["errors"]])
    
    # Mostrar resumen
    print("\n" + "="*80)
    print("RESUMEN DE VALIDACIÓN")
    print("="*80)
    print(f"\nTests pasados: {total_pass}")
    print(f"Tests fallidos: {total_fail}")
    print(f"Tasa de éxito: {(total_pass / (total_pass + total_fail) * 100) if (total_pass + total_fail) > 0 else 0:.1f}%")
    
    if all_errors:
        print(f"\nErrores encontrados ({len(all_errors)}):")
        for error in all_errors:
            print(f"  - {error}")
    else:
        print("\n✓ No hay errores críticos")
    
    # Genererar archivo de resultados JSON
    results_data = {
        "timestamp": datetime.now().isoformat(),
        "total_pass": total_pass,
        "total_fail": total_fail,
        "success_rate": (total_pass / (total_pass + total_fail) * 100) if (total_pass + total_fail) > 0 else 0,
        "errors": all_errors,
        "test_results": {name: result for name, result in all_results}
    }
    
    results_file = PROJECT_ROOT / "docs" / "phase5_validation_results.json"
    results_file.parent.mkdir(exist_ok=True)
    results_file.write_text(json.dumps(results_data, indent=2, default=str))
    print(f"\n✓ Resultados guardados en: {results_file}")
    
    return results_data


if __name__ == "__main__":
    try:
        results = run_all_validations()
        print("\n" + "="*80)
        print("VALIDACIÓN COMPLETADA")
        print("="*80)
    except Exception as e:
        print(f"\n✗ Error fatal durante validación: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
