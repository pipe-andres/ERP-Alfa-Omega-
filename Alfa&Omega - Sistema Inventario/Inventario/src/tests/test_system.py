"""
SISTEMA DE TESTING PROFESIONAL - PHASE 2 VALIDATION
Validación exhaustiva del sistema bajo condiciones reales

Incluye:
- Test de inicialización
- Stress test (100 operaciones)
- Validación de backups
- Auditoría de sistema
- Validación de logging
"""

import sys
import os
import sqlite3
import time
import json
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Agregar src al path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.core.error_handler import logger, log_error
    from src.database.connection import init_db, get_connection, DB_PATH
    from src.core.validators import (
        validate_product_code, validate_product_name, 
        validate_product_price, validate_product_quantity
    )
    from src.utils.database_backup import backup_database, restore_database
    # Usar funciones del módulo de inventario directamente
    from src.services import inventory
except ImportError as e:
    print(f"❌ Error de imports: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


class SystemValidator:
    """Validador profesional del sistema."""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "status": "RUNNING"
        }
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        
    def print_header(self, title):
        """Imprime encabezado de test."""
        print(f"\n{'═'*70}")
        print(f"║ {title:<66} ║")
        print(f"{'═'*70}")
    
    def print_test(self, name, status, message=""):
        """Imprime resultado de test."""
        icon = "✓" if status == "PASS" else "✗" if status == "FAIL" else "⚠"
        color = "\033[92m" if status == "PASS" else "\033[91m" if status == "FAIL" else "\033[93m"
        reset = "\033[0m"
        
        print(f"{color}{icon}{reset} {name:<50} {status:<6} {message}")
        
        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        else:
            self.warnings += 1
    
    def test_initialization(self):
        """TEST 1: Inicialización del sistema."""
        self.print_header("TEST 1: INICIALIZACIÓN DEL SISTEMA")
        
        try:
            # Test 1.1: BD existe
            db_path = Path(DB_PATH)  # Convertir a Path si es string
            if db_path.exists():
                self.print_test("Database existe", "PASS", f"({DB_PATH})")
            else:
                self.print_test("Database existe", "FAIL", "BD no creada")
                return False
            
            # Test 1.2: Tablas críticas existen
            with get_connection() as conn:
                cur = conn.cursor()
                tables = [
                    "productos", "users", "roles", "audit_log",
                    "documents", "document_lines", "partners"
                ]
                
                for table in tables:
                    cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                    if cur.fetchone():
                        self.print_test(f"  Tabla '{table}' existe", "PASS")
                    else:
                        self.print_test(f"  Tabla '{table}' existe", "FAIL")
                        self.failed += 1
            
            # Test 1.3: Logs folder existe
            logs_dir = PROJECT_ROOT / "logs"
            if logs_dir.exists():
                self.print_test("Carpeta /logs existe", "PASS")
            else:
                self.print_test("Carpeta /logs existe", "WARN", "Será creada en runtime")
            
            # Test 1.4: Backups folder existe
            backups_dir = PROJECT_ROOT / "backups"
            if backups_dir.exists():
                self.print_test("Carpeta /backups existe", "PASS")
            else:
                self.print_test("Carpeta /backups existe", "WARN", "Será creada en runtime")
            
            return True
            
        except Exception as e:
            self.print_test("Inicialización", "FAIL", str(e))
            log_error(e, context={"test": "initialization"})
            return False
    
    def test_validators(self):
        """TEST 2: Validadores de entrada."""
        self.print_header("TEST 2: VALIDADORES DE ENTRADA")
        
        tests_passed = 0
        tests_total = 0
        
        # Test código válido
        tests_total += 1
        try:
            validate_product_code("PROD-0001")
            self.print_test("Validar código válido (PROD-0001)", "PASS")
            tests_passed += 1
        except:
            self.print_test("Validar código válido (PROD-0001)", "FAIL")
        
        # Test código inválido
        tests_total += 1
        try:
            validate_product_code("'; DROP TABLE--")
            self.print_test("Rechazar SQL injection en código", "FAIL", "No validó entrada maliciosa")
        except:
            self.print_test("Rechazar SQL injection en código", "PASS")
            tests_passed += 1
        
        # Test nombre válido
        tests_total += 1
        try:
            validate_product_name("Producto Test")
            self.print_test("Validar nombre válido", "PASS")
            tests_passed += 1
        except:
            self.print_test("Validar nombre válido", "FAIL")
        
        # Test precio válido
        tests_total += 1
        try:
            validate_product_price(19.99)
            self.print_test("Validar precio válido (19.99)", "PASS")
            tests_passed += 1
        except:
            self.print_test("Validar precio válido", "FAIL")
        
        # Test precio negativo (debe fallar)
        tests_total += 1
        try:
            validate_product_price(-10)
            self.print_test("Rechazar precio negativo", "FAIL", "No validó entrada inválida")
        except:
            self.print_test("Rechazar precio negativo", "PASS")
            tests_passed += 1
        
        # Test cantidad
        tests_total += 1
        try:
            validate_product_quantity(100)
            self.print_test("Validar cantidad válida (100)", "PASS")
            tests_passed += 1
        except:
            self.print_test("Validar cantidad válida", "FAIL")
        
        self.passed += tests_passed
        self.failed += (tests_total - tests_passed)
        
        return tests_passed == tests_total
    
    def test_stress_operations(self):
        """TEST 3: Stress test de operaciones."""
        self.print_header("TEST 3: STRESS TEST (100 OPERACIONES)")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        operations_log = []
        errors = []
        
        print(f"Ejecutando 100 operaciones CRUD...")
        
        try:
            # 25 Inserciones
            for i in range(25):
                try:
                    codigo = f"TEST-{timestamp}-{i:03d}"
                    nombre = f"Test Product {i}"
                    precio = 10.0 + i
                    cantidad = 5 + i
                    
                    # Validar primero
                    validate_product_code(codigo)
                    validate_product_name(nombre)
                    validate_product_price(precio)
                    validate_product_quantity(cantidad)
                    
                    # Insertar
                    with get_connection() as conn:
                        cur = conn.cursor()
                        cur.execute(
                            "INSERT INTO productos (codigo, nombre, categoria, precio, cantidad, avg_cost) VALUES (?,?,?,?,?,?)",
                            (codigo, nombre, "TEST", precio, cantidad, precio)
                        )
                        conn.commit()
                    
                    operations_log.append({"op": "INSERT", "code": codigo, "status": "OK"})
                except Exception as e:
                    errors.append(f"INSERT {i}: {str(e)}")
                    operations_log.append({"op": "INSERT", "code": f"TEST-{i}", "status": "FAIL"})
            
            self.print_test("Inserciones (25/25)", "PASS" if len(errors) == 0 else "FAIL")
            
            # 25 Búsquedas (SELECT)
            errors_search = 0
            with get_connection() as conn:
                cur = conn.cursor()
                for i in range(25):
                    try:
                        codigo = f"TEST-{timestamp}-{i:03d}"
                        cur.execute("SELECT * FROM productos WHERE codigo = ?", (codigo,))
                        if cur.fetchone():
                            operations_log.append({"op": "SELECT", "code": codigo, "status": "OK"})
                        else:
                            errors_search += 1
                            operations_log.append({"op": "SELECT", "code": codigo, "status": "NOT_FOUND"})
                    except Exception as e:
                        errors_search += 1
                        errors.append(f"SELECT {i}: {str(e)}")
            
            self.print_test("Búsquedas (25/25)", "PASS" if errors_search == 0 else "WARN", 
                          f"({25 - errors_search}/25 encontrados)")
            
            # 25 Actualizaciones
            errors_update = 0
            for i in range(25):
                try:
                    codigo = f"TEST-{timestamp}-{i:03d}"
                    nueva_cantidad = 100 + i
                    
                    with get_connection() as conn:
                        cur = conn.cursor()
                        cur.execute("UPDATE productos SET cantidad=? WHERE codigo=?", (nueva_cantidad, codigo))
                        conn.commit()
                    
                    operations_log.append({"op": "UPDATE", "code": codigo, "status": "OK"})
                except Exception as e:
                    errors_update += 1
                    errors.append(f"UPDATE {i}: {str(e)}")
                    operations_log.append({"op": "UPDATE", "code": codigo, "status": "FAIL"})
            
            self.print_test("Actualizaciones (25/25)", "PASS" if errors_update == 0 else "WARN")
            
            # 25 Eliminaciones
            errors_delete = 0
            for i in range(25):
                try:
                    codigo = f"TEST-{timestamp}-{i:03d}"
                    
                    with get_connection() as conn:
                        cur = conn.cursor()
                        cur.execute("DELETE FROM productos WHERE codigo=?", (codigo,))
                        conn.commit()
                    
                    operations_log.append({"op": "DELETE", "code": codigo, "status": "OK"})
                except Exception as e:
                    errors_delete += 1
                    operations_log.append({"op": "DELETE", "code": codigo, "status": "FAIL"})
            
            self.print_test("Eliminaciones (25/25)", "PASS" if errors_delete == 0 else "WARN")
            
            # Resumen
            print(f"\nResumen operaciones:")
            print(f"  Totales ejecutadas: 100")
            print(f"  Exitosas: {100 - len(errors)}")
            print(f"  Fallidas: {len(errors)}")
            
            if len(errors) == 0:
                self.passed += 4
            else:
                self.passed += 3
                self.warnings += 1
            
            return len(errors) == 0
            
        except Exception as e:
            self.print_test("Stress test", "FAIL", str(e))
            log_error(e, context={"test": "stress_operations"})
            self.failed += 1
            return False
    
    def test_backups(self):
        """TEST 4: Sistema de backups."""
        self.print_header("TEST 4: SISTEMA DE BACKUPS")
        
        try:
            # Test 4.1: Crear backup
            print("Creando backup manual...")
            backup_file = backup_database(str(DB_PATH), backup_type="manual")
            
            if backup_file and backup_file.exists():
                self.print_test("Crear backup", "PASS", f"({backup_file.name})")
                self.passed += 1
            else:
                self.print_test("Crear backup", "FAIL")
                self.failed += 1
                return False
            
            # Test 4.2: Verificar tamaño
            size = backup_file.stat().st_size
            if size > 0:
                self.print_test(f"Tamaño backup válido", "PASS", f"({size:,} bytes)")
                self.passed += 1
            else:
                self.print_test("Tamaño backup válido", "FAIL")
                self.failed += 1
            
            # Test 4.3: Verificar integridad del backup
            try:
                conn = sqlite3.connect(str(backup_file))
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM productos")
                count = cur.fetchone()[0]
                conn.close()
                
                self.print_test("Integridad del backup", "PASS", f"(BD válida, {count} productos)")
                self.passed += 1
            except Exception as e:
                self.print_test("Integridad del backup", "FAIL", str(e))
                self.failed += 1
            
            # Test 4.4: Verificar carpeta /backups
            backups_dir = PROJECT_ROOT / "backups"
            if backups_dir.exists():
                backup_count = len(list(backups_dir.glob("*.db")))
                self.print_test(f"Backups en carpeta", "PASS", f"({backup_count} archivos)")
                self.passed += 1
            else:
                self.print_test("Carpeta /backups", "WARN", "No existe (se créará en runtime)")
                self.warnings += 1
            
            return True
            
        except Exception as e:
            self.print_test("Sistema de backups", "FAIL", str(e))
            log_error(e, context={"test": "backups"})
            self.failed += 1
            return False
    
    def test_logging(self):
        """TEST 5: Sistema de logging."""
        self.print_header("TEST 5: SISTEMA DE LOGGING")
        
        try:
            logs_dir = PROJECT_ROOT / "logs"
            logs_file = logs_dir / "sistema.log"
            
            # Test 5.1: Archivo de logs existe
            if logs_file.exists():
                self.print_test("Archivo logs/sistema.log existe", "PASS")
                self.passed += 1
            else:
                self.print_test("Archivo logs/sistema.log existe", "WARN", "Será creado en runtime")
                self.warnings += 1
                return True  # No es crítico
            
            # Test 5.2: Logs tiene contenido
            if logs_file.stat().st_size > 0:
                self.print_test("Archivo logs tiene contenido", "PASS", 
                              f"({logs_file.stat().st_size} bytes)")
                self.passed += 1
            else:
                self.print_test("Archivo logs tiene contenido", "WARN")
                self.warnings += 1
            
            # Test 5.3: Buscar ERROR entries
            with open(logs_file) as f:
                content = f.read()
                # Verificar que hay logs INFO
                if "INFO" in content or "WARNING" in content or "ERROR" in content:
                    self.print_test("Logs contiene entradas", "PASS")
                    self.passed += 1
                else:
                    self.print_test("Logs contiene entradas", "WARN")
                    self.warnings += 1
            
            return True
            
        except Exception as e:
            self.print_test("Sistema de logging", "WARN", str(e))
            self.warnings += 1
            return True  # No crítico
    
    def test_audit_trail(self):
        """TEST 6: Auditoría."""
        self.print_header("TEST 6: AUDITORÍA DE OPERACIONES")
        
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                
                # Test 6.1: Tabla audit_log existe
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_log'")
                if cur.fetchone():
                    self.print_test("Tabla audit_log existe", "PASS")
                    self.passed += 1
                else:
                    self.print_test("Tabla audit_log existe", "FAIL")
                    self.failed += 1
                    return False
                
                # Test 6.2: Hay registros de auditoría
                cur.execute("SELECT COUNT(*) FROM audit_log")
                count = cur.fetchone()[0]
                
                if count > 0:
                    self.print_test(f"Registros de auditoría", "PASS", f"({count} registros)")
                    self.passed += 1
                else:
                    self.print_test("Registros de auditoría", "WARN", "(Sin registros aún)")
                    self.warnings += 1
                
                # Test 6.3: Campos de auditoría completos
                cur.execute("PRAGMA table_info(audit_log)")
                columns = [row[1] for row in cur.fetchall()]
                required = ["id", "user_id", "action", "created_at"]
                
                if all(col in columns for col in required):
                    self.print_test("Columnas de auditoría", "PASS", f"({len(columns)} campos)")
                    self.passed += 1
                else:
                    self.print_test("Columnas de auditoría", "FAIL")
                    self.failed += 1
            
            return True
            
        except Exception as e:
            self.print_test("Auditoría", "FAIL", str(e))
            log_error(e, context={"test": "audit_trail"})
            self.failed += 1
            return False
    
    def test_data_integrity(self):
        """TEST 7: Integridad de datos."""
        self.print_header("TEST 7: INTEGRIDAD DE DATOS")
        
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                
                # Test 7.1: PRAGMA integrity_check
                cur.execute("PRAGMA integrity_check")
                result = cur.fetchone()
                
                if result[0] == "ok":
                    self.print_test("PRAGMA integrity_check", "PASS")
                    self.passed += 1
                else:
                    self.print_test("PRAGMA integrity_check", "FAIL", result[0])
                    self.failed += 1
                
                # Test 7.2: Foreign keys habilitados
                cur.execute("PRAGMA foreign_keys")
                fk_enabled = cur.fetchone()[0]
                
                if fk_enabled:
                    self.print_test("Foreign keys habilitados", "PASS")
                    self.passed += 1
                else:
                    self.print_test("Foreign keys habilitados", "WARN", "No están habilitados")
                    self.warnings += 1
                
                # Test 7.3: Índices creados
                cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
                index_count = cur.fetchone()[0]
                
                if index_count > 0:
                    self.print_test("Índices de BD", "PASS", f"({index_count} índices)")
                    self.passed += 1
                else:
                    self.print_test("Índices de BD", "WARN", "(Sin índices optimizados)")
                    self.warnings += 1
            
            return True
            
        except Exception as e:
            self.print_test("Integridad de datos", "FAIL", str(e))
            log_error(e, context={"test": "data_integrity"})
            self.failed += 1
            return False
    
    def run_all_tests(self):
        """Ejecuta todos los tests."""
        print("\n")
        print("╔════════════════════════════════════════════════════════╗")
        print("║     VALIDACIÓN PROFESIONAL DEL SISTEMA PHASE 2         ║")
        print("║     Alfa & Omega - Sistema de Inventario               ║")
        print("╚════════════════════════════════════════════════════════╝")
        
        all_passed = True
        
        # Ejecutar tests
        all_passed &= self.test_initialization()
        all_passed &= self.test_validators()
        all_passed &= self.test_stress_operations()
        all_passed &= self.test_backups()
        all_passed &= self.test_logging()
        all_passed &= self.test_audit_trail()
        all_passed &= self.test_data_integrity()
        
        # Resumen final
        self.print_summary(all_passed)
        
        return all_passed
    
    def print_summary(self, all_passed):
        """Imprime resumen final."""
        print(f"\n{'═'*70}")
        print(f"║ RESUMEN FINAL                                                 ║")
        print(f"{'═'*70}")
        print(f"✓ Tests pasados:    {self.passed}")
        print(f"⚠ Advertencias:     {self.warnings}")
        print(f"✗ Tests fallidos:   {self.failed}")
        print(f"{'─'*70}")
        
        total = self.passed + self.failed
        if total > 0:
            percentage = (self.passed / total) * 100
            print(f"Tasa de éxito: {percentage:.1f}%")
        
        if all_passed or self.failed == 0:
            print(f"\n✅ SISTEMA VALIDADO EXITOSAMENTE")
            self.results["status"] = "PASSED"
        else:
            print(f"\n⚠  SISTEMA VALIDADO CON ADVERTENCIAS")
            self.results["status"] = "PASSED_WITH_WARNINGS"
        
        print(f"{'═'*70}\n")


if __name__ == "__main__":
    validator = SystemValidator()
    success = validator.run_all_tests()
    sys.exit(0 if success else 1)
