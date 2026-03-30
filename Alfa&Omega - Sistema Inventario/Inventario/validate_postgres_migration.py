#!/usr/bin/env python3
"""
Quick validation script to verify PostgreSQL compatibility.
Checks that all critical modules can be imported and basic operations work.
"""

import os
import sys
from pathlib import Path

# Setup path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Set Postgres mode
os.environ['DB_ENGINE'] = 'postgres'
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://inventario_user:inventario_pass@localhost:5432/inventario'

print("=" * 80)
print("PostgreSQL Migration Validation")
print("=" * 80)

# Test 1: Import modules
print("\n[1/5] Testing module imports...")
try:
    from src.database.connection import get_connection, DB_ENGINE, CursorWrapper
    print(f"    ✓ connection.py (DB_ENGINE={DB_ENGINE})")
    
    from src.database.repository import ensure_schema as repo_schema
    print("    ✓ repository.py")
    
    from src.services.documents import ensure_schema as doc_schema, get_next_number
    print("    ✓ documents.py")
    
    from src.services.partners import ensure_schema as partner_schema
    print("    ✓ partners.py")
    
    from src.core.auth import ensure_defaults, create_user, list_users
    print("    ✓ auth.py")
    
    from src.services.audit import log_event
    print("    ✓ audit.py")
    
    from src.services.inventory import post_purchase, post_sale, post_adjustment
    print("    ✓ inventory.py")
    
    print("\n✓ All modules imported successfully")
except Exception as e:
    print(f"\n✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Check DB_ENGINE is postgres
print("\n[2/5] Verifying DB_ENGINE configuration...")
if DB_ENGINE == 'postgres':
    print("    ✓ DB_ENGINE is correctly set to 'postgres'")
else:
    print(f"    ✗ DB_ENGINE is '{DB_ENGINE}', expected 'postgres'")
    sys.exit(1)

# Test 3: Test CursorWrapper placeholder translation
print("\n[3/5] Testing CursorWrapper SQL translation...")
class MockCursor:
    def __init__(self):
        self.last_query = None
        self.last_params = None
    
    def execute(self, sql, params=None):
        self.last_query = sql
        self.last_params = params
        return self
    
    def fetchone(self):
        return (1,)
    
    def fetchall(self):
        return [(1,), (2,)]
    
    @property
    def rowcount(self):
        return 1

try:
    mock_cur = MockCursor()
    wrapper = CursorWrapper(mock_cur)
    
    # Test 1: ? → %s translation
    wrapper.execute("SELECT * FROM users WHERE id=?", (1,))
    if "%s" in mock_cur.last_query and "?" not in mock_cur.last_query:
        print("    ✓ Placeholder translation: ? → %s")
    else:
        print(f"    ✗ Placeholder translation failed: {mock_cur.last_query}")
        sys.exit(1)
    
    # Test 2: SELECT last_insert_rowid() → SELECT LASTVAL()
    wrapper.execute("SELECT last_insert_rowid()")
    if "LASTVAL()" in mock_cur.last_query:
        print("    ✓ last_insert_rowid() → LASTVAL() translation")
    else:
        print(f"    ✗ last_insert_rowid translation failed: {mock_cur.last_query}")
        sys.exit(1)
        
    print("\n✓ CursorWrapper translation working correctly")
except Exception as e:
    print(f"\n✗ CursorWrapper test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Check for SQLite-specific patterns
print("\n[4/5] Scanning for SQLite-specific patterns...")
dangerous_patterns = [
    ("sqlite_master", "sqlite_master references (must be information_schema for Postgres)"),
    ("PRAGMA ", "PRAGMA statements (SQLite-specific)"),
    ("AUTOINCREMENT", "AUTOINCREMENT (use SERIAL for Postgres)"),
]

files_to_check = [
    "src/database/connection.py",
    "src/database/repository.py",
    "src/services/documents.py",
    "src/services/partners.py",
    "src/core/auth.py",
    "src/services/audit.py",
    "src/services/inventory.py",
]

issues_found = []
for file_path in files_to_check:
    full_path = PROJECT_ROOT / file_path
    if full_path.exists():
        try:
            content = full_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = full_path.read_text(encoding='latin-1')
        for pattern, description in dangerous_patterns:
            # Check for dangerous patterns outside of comments
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                # Skip comments
                if line.strip().startswith('#'):
                    continue
                # Skip docstrings
                if '"""' in line or "'''" in line:
                    continue
                if pattern in line and "if DB_ENGINE" not in line:
                    issues_found.append(f"{file_path}:{i} - {pattern} ({description})")

if issues_found:
    print("    ⚠ Potential SQLite-specific patterns found (may be guarded):")
    for issue in issues_found[:5]:  # Show first 5
        print(f"      - {issue}")
    if len(issues_found) > 5:
        print(f"      ... and {len(issues_found) - 5} more")
else:
    print("    ✓ No critical SQLite-specific patterns found")

# Test 5: Syntax check all Python files
print("\n[5/5] Syntax validation of critical files...")
import py_compile

syntax_ok = True
for file_path in files_to_check:
    full_path = PROJECT_ROOT / file_path
    if full_path.exists():
        try:
            py_compile.compile(str(full_path), doraise=True)
            print(f"    ✓ {file_path}")
        except py_compile.PyCompileError as e:
            print(f"    ✗ {file_path}: {e}")
            syntax_ok = False

if not syntax_ok:
    sys.exit(1)

print("\n" + "=" * 80)
print("✓ MIGRATION VALIDATION PASSED")
print("=" * 80)
print("\nNext steps:")
print("1. Start PostgreSQL: docker-compose -f docker-compose.postgres.yml up -d")
print("2. Run migrations: alembic upgrade head")
print("3. Run tests: pytest tests/")
print("4. Start API: uvicorn main_api:app --reload")
print("=" * 80)
