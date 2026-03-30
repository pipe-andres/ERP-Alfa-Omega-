"""Simple health check utility for the inventory system.
Provides a human‑readable report of critical subsystems.
"""

from config import settings
from src.database.connection import get_connection
import os


def check_database():
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1")
        return True, "connection ok"
    except Exception as e:
        return False, f"db error: {e}"


def check_permissions():
    issues = []
    for p in (settings.DATA_DIR, settings.LOG_DIR, settings.BACKUP_DIR):
        try:
            if not os.access(p, os.W_OK):
                issues.append(f"no write permission: {p}")
        except Exception as e:
            issues.append(f"error checking {p}: {e}")
    return (len(issues) == 0), issues


def check_logs():
    log_file = settings.LOG_DIR / "sistema.log"
    if log_file.exists():
        size = log_file.stat().st_size
        return True, f"exists ({size} bytes)"
    return False, "missing"


def check_backups():
    files = list(settings.BACKUP_DIR.glob("*.db"))
    count = len(files)
    sample = [str(f.name) for f in files[:5]]
    return count, sample


def check_integrity():
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA integrity_check;")
            res = cur.fetchone()[0]
        return res == "ok", res
    except Exception as e:
        return False, str(e)


def main():
    print("=== SYSTEM HEALTH CHECK ===")
    ok, msg = check_database()
    print(f"Database connection: {'OK' if ok else 'FAIL'} - {msg}")

    ok, issues = check_permissions()
    if ok:
        print("Filesystem permissions: OK")
    else:
        print("Filesystem permissions: FAIL")
        for i in issues:
            print(f"  - {i}")

    ok, msg = check_logs()
    print(f"Log file: {'OK' if ok else 'MISSING'} - {msg}")

    count, sample = check_backups()
    print(f"Backups present: {count} files")
    if sample:
        print("  examples:")
        for s in sample:
            print(f"   - {s}")

    ok, integrity = check_integrity()
    print(f"Integrity check: {'OK' if ok else 'FAIL'} - {integrity}")

    print("=== END HEALTH CHECK ===")


if __name__ == "__main__":
    main()
