# core/backup.py
import os
import sqlite3
import shutil
from core.database import get_connection, DB_PATH

def backup_db(target_path: str):
    os.makedirs(os.path.dirname(target_path) or ".", exist_ok=True)
    with get_connection() as src:
        with sqlite3.connect(target_path) as dest:
            src.backup(dest)  # copia segura en caliente

def restore_db(source_path: str):
    if not os.path.exists(source_path):
        raise FileNotFoundError(source_path)
    shutil.copy2(source_path, DB_PATH)
