"""Diagnostic panel for support teams.
Provides counters, file sizes and recent errors.
"""

from config import settings
from src.database.connection import get_connection
from pathlib import Path


def get_db_size():
    try:
        path = Path(settings.DB_PATH)
        return path.stat().st_size
    except Exception:
        return None


def table_record_counts():
    counts = {}
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cur.fetchall()]
            for t in tables:
                cur.execute(f"SELECT COUNT(*) FROM {t}")
                counts[t] = cur.fetchone()[0]
    except Exception:
        pass
    return counts


def backup_status():
    files = list(settings.BACKUP_DIR.glob("*.db"))
    total = len(files)
    sizes = {f.name: f.stat().st_size for f in files}
    return total, sizes


def recent_errors(n: int = 20):
    log_file = settings.LOG_DIR / "sistema.log"
    if not log_file.exists():
        return []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # filter for ERROR lines
        errs = [l for l in lines if "ERROR" in l][-n:]
        return errs
    except Exception:
        return []


def main():
    print("=== SYSTEM DIAGNOSTICS ===")
    size = get_db_size()
    print(f"DB size: {size if size is not None else 'unknown'} bytes")

    counts = table_record_counts()
    print("Record counts per table:")
    for t, c in counts.items():
        print(f"  {t}: {c}")

    total, sizes = backup_status()
    print(f"Backups: {total} files")
    for n, s in sizes.items():
        print(f"  {n}: {s} bytes")

    errs = recent_errors()
    print(f"Recent error log entries ({len(errs)}):")
    for l in errs:
        print(f"  {l.strip()}")

    print("=== END DIAGNOSTICS ===")

if __name__ == "__main__":
    main()
