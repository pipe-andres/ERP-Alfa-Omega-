#!/usr/bin/env python3
"""
Reorganize Alfa & Omega Inventario project to modern architecture.
This script automates the migration from flat structure to /src/* structure.
"""
import os
import shutil
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
SRC_DIR = PROJECT_ROOT / "src"

def safe_copy_and_update(src_file: Path, dst_file: Path, import_replacements: dict):
    """Read file, apply import replacements, and write to destination."""
    print(f"  Moving: {src_file.name} → {dst_file.relative_to(PROJECT_ROOT)}")
    
    if src_file.exists():
        content = src_file.read_text(encoding='utf-8', errors='ignore')
        
        # Apply import replacements
        for old, new in import_replacements.items():
            content = re.sub(
                r'\bfrom\s+' + re.escape(old) + r'\s+import',
                f'from {new} import',
                content
            )
            content = re.sub(
                r'\bimport\s+' + re.escape(old),
                f'import {new}',
                content
            )
        
        dst_file.write_text(content, encoding='utf-8')
        return True
    return False

def reorganize():
    """Execute full reorganization."""
    print("=" * 70)
    print("REORGANIZANDO: Alfa & Omega Inventario → Arquitectura Moderna")
    print("=" * 70)
    
    # Phase 1: Copy database layer
    print("\n[PHASE 1] Database Layer → src/database/")
    replacements_db = {}
    safe_copy_and_update(
        PROJECT_ROOT / "core" / "database.py",
        SRC_DIR / "database" / "connection.py",
        replacements_db
    )
    
    # Phase 2: Copy core layer (auth, with bcrypt upgrade)
    print("\n[PHASE 2] Core Auth → src/core/")
    replacements_core_auth = {
        "core.database": "src.database.connection"
    }
    
    if (PROJECT_ROOT / "core" / "auth.py").exists():
        content = (PROJECT_ROOT / "core" / "auth.py").read_text(encoding='utf-8', errors='ignore')
        
        # Upgrade password hashing to bcrypt
        old_hash_code = '''def _hash_password(password: str, *, salt: Optional[str] = None) -> str:
    """
    Genera un hash con esquema: algo:sha256:salt:hashhex
    """
    if not salt:
        salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"algo:sha256:{salt}:{h}"

def _verify_password(stored: str, password: str) -> bool:
    try:
        algo, algoname, salt, hexhash = stored.split(":", 3)
        if algoname != "sha256":
            return False
        h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return secrets.compare_digest(h, hexhash)
    except Exception:
        return False'''
        
        new_hash_code = '''from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _hash_password(password: str) -> str:
    """Hash password using bcrypt via passlib."""
    return pwd_context.hash(password)

def _verify_password(stored: str, password: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        return pwd_context.verify(password, stored)
    except Exception:
        return False'''
        
        if old_hash_code in content:
            content = content.replace(old_hash_code, new_hash_code)
            print("  ✓ Upgraded password hashing to bcrypt")
        
        # Remove old imports if present
        content = re.sub(r'import hashlib\n', '', content)
        content = re.sub(r'import secrets\n', '', content)
        
        # Update database import
        for old, new in replacements_core_auth.items():
            content = re.sub(
                r'\bfrom\s+' + re.escape(old) + r'\s+import',
                f'from {new} import',
                content
            )
        
        (SRC_DIR / "core" / "auth.py").write_text(content, encoding='utf-8')
        print("  ✓ core/auth.py → src/core/auth.py (with bcrypt upgrade)")
    
    # Phase 3: Copy services layer
    print("\n[PHASE 3] Services Layer → src/services/")
    
    service_files = {
        "audit.py": {
            "core.database": "src.database.connection"
        },
        "services.py": {
            "core.database": "src.database.connection",
            "core.audit": "src.services.audit",
            "core.documents": "src.services.documents",
            "core.partners": "src.services.partners"
        },
        "documents.py": {
            "core.database": "src.database.connection",
            "core.partners": "src.services.partners"
        },
        "partners.py": {
            "core.database": "src.database.connection"
        },
        "reports.py": {
            "core.database": "src.database.connection"
        }
    }
    
    for filename, replacements in service_files.items():
        src_file = PROJECT_ROOT / "core" / filename
        dst_name = "inventory.py" if filename == "services.py" else filename
        dst_file = SRC_DIR / "services" / dst_name
        safe_copy_and_update(src_file, dst_file, replacements)
    
    # Phase 4: Copy utilities
    print("\n[PHASE 4] Utilities → src/utils/")
    safe_copy_and_update(
        PROJECT_ROOT / "core" / "backup.py",
        SRC_DIR / "utils" / "backup.py",
        {"core.database": "src.database.connection"}
    )
    
    # Phase 5: Copy database settings
    print("\n[PHASE 5] Database Settings → src/database/")
    safe_copy_and_update(
        PROJECT_ROOT / "core" / "settings.py",
        SRC_DIR / "database" / "settings.py",
        {"core.database": "src.database.connection"}
    )
    
    # Phase 6: Copy UI/Styles
    print("\n[PHASE 6] UI & Styles → src/app/")
    
    # Copy styles
    if (PROJECT_ROOT / "diseño" / "estilo.py").exists():
        shutil.copy(
            PROJECT_ROOT / "diseño" / "estilo.py",
            SRC_DIR / "app" / "styles" / "theme.py"
        )
        print("  ✓ diseño/estilo.py → src/app/styles/theme.py")
    
    if (PROJECT_ROOT / "diseño" / "scrollbars.py").exists():
        shutil.copy(
            PROJECT_ROOT / "diseño" / "scrollbars.py",
            SRC_DIR / "app" / "styles" / "scrollbars.py"
        )
        print("  ✓ diseño/scrollbars.py → src/app/styles/scrollbars.py")
    
    # Copy and update main GUI
    if (PROJECT_ROOT / "app" / "gui.py").exists():
        content = (PROJECT_ROOT / "app" / "gui.py").read_text(encoding='utf-8', errors='ignore')
        
        replacements_gui = {
            "diseño.estilo": "src.app.styles.theme",
            "diseño.scrollbars": "src.app.styles.scrollbars",
            "core.audit": "src.services.audit",
            "core.auth": "src.core.auth",
            "core.services": "src.services.inventory",
            "core.reports": "src.services.reports",
            "core.documents": "src.services.documents",
            "core.partners": "src.services.partners",
            "core.settings": "src.database.settings"
        }
        
        # Replace imports
        for old, new in replacements_gui.items():
            content = re.sub(
                r'\bfrom\s+' + re.escape(old) + r'\s+import',
                f'from {new} import',
                content
            )
        
        # Update module references (estilo → theme)
        content = content.replace("estilo.aplicar_estilo_treeview", "theme.aplicar_estilo_treeview")
        content = content.replace("from .styles import theme", "from .styles import theme")
        
        (SRC_DIR / "app" / "main_window.py").write_text(content, encoding='utf-8')
        print("  ✓ app/gui.py → src/app/main_window.py (imports updated)")
    
    # Phase 7: Update root entry points
    print("\n[PHASE 7] Update Root Entry Points")
    
    # Update main.py
    if (PROJECT_ROOT / "main.py").exists():
        content = (PROJECT_ROOT / "main.py").read_text(encoding='utf-8', errors='ignore')
        
        replacements_main = {
            "core.database": "src.database.connection",
            "core.auth": "src.core.auth",
            "core.partners": "src.services.partners",
            "core.settings": "src.database.settings",
            "app.gui": "src.app.main_window",
        }
        
        for old, new in replacements_main.items():
            content = re.sub(
                r'\bfrom\s+' + re.escape(old) + r'\s+import',
                f'from {new} import',
                content
            )
        
        (PROJECT_ROOT / "main.py").write_text(content, encoding='utf-8')
        print("  ✓ main.py (imports updated)")
    
    # Phase 8: Copy assets
    print("\n[PHASE 8] Copy Assets → src/assets/")
    assets_src = PROJECT_ROOT / "assets"
    assets_dst = SRC_DIR / "assets"
    
    if assets_src.exists() and assets_src.is_dir():
        for item in assets_src.iterdir():
            if item.is_file():
                shutil.copy(item, assets_dst / item.name)
        print(f"  ✓ Copied {len(list(assets_src.iterdir()))} asset files")
    
    # Phase 9: Validation
    print("\n[PHASE 9] Validation")
    
    # Check syntax of key files
    import py_compile
    key_files = [
        SRC_DIR / "database" / "connection.py",
        SRC_DIR / "core" / "auth.py",
        SRC_DIR / "services" / "inventory.py",
        SRC_DIR / "app" / "main_window.py",
        PROJECT_ROOT / "main.py"
    ]
    
    errors = []
    for file in key_files:
        if file.exists():
            try:
                py_compile.compile(str(file), doraise=True)
                print(f"  ✓ {file.relative_to(PROJECT_ROOT)} [OK]")
            except py_compile.PyCompileError as e:
                print(f"  ✗ {file.relative_to(PROJECT_ROOT)} [SYNTAX ERROR]")
                errors.append((file, e))
    
    if errors:
        print("\n⚠️  SYNTAX ERRORS DETECTED:")
        for file, error in errors:
            print(f"  {file}: {error}")
    
    # Phase 10: Cleanup old files
    print("\n[PHASE 10] Cleanup (Optional)")
    print("  Note: Old files in /core, /app, /diseño are NOT deleted.")
    print("  Keep them until validation is complete, then manually remove.")
    
    print("\n" + "=" * 70)
    print("✓ REORGANIZATION COMPLETE!")
    print("=" * 70)
    print("\nNEXT STEPS:")
    print("1. Test: python main.py")
    print("2. If working, delete old folders: core/, app/, diseño/")
    print("3. Update requirements.txt to include 'passlib'")
    print("4. Run: pip install passlib")
    print("=" * 70)

if __name__ == "__main__":
    reorganize()
