"""Utilities for gathering system status used by GUI and diagnostics."""
from pathlib import Path
from typing import Dict

from src.core import license_manager, update_manager
from config import settings


def get_system_info() -> Dict[str, str]:
    """Return a dictionary of system status items.

    Keys include:
    - license_valid (bool)
    - local_version (str)
    - backup_count (int)
    - recent_logs (str)
    """
    info: Dict[str, str] = {}
    info["license_valid"] = license_manager.validate_license()
    info["local_version"] = update_manager.get_local_version()

    try:
        bk_files = list(settings.BACKUP_DIR.glob("*.db"))
        info["backup_count"] = len(bk_files)
    except Exception:
        info["backup_count"] = 0

    try:
        with open(settings.LOG_DIR / "sistema.log", "r", encoding="utf-8") as f:
            lines = f.readlines()
        info["recent_logs"] = "".join(lines[-3:])
    except Exception:
        info["recent_logs"] = "(no disponible)"
    return info
