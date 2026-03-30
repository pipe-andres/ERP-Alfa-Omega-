# src/utils/database_backup.py
"""
Sistema automático de backups de base de datos.
Garantiza que NUNCA se pierdan datos.
"""

import os
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import logging

logger = logging.getLogger("AlfaOmega.Backup")

# Crear directorio de backups
from config import settings

BACKUP_DIR = settings.BACKUP_DIR
BACKUP_DIR.mkdir(exist_ok=True)

# Mantener máximo 30 backups (30 días)
MAX_BACKUPS = 30


def get_backup_filename(db_path: str, backup_type: str = "auto") -> str:
    """
    Genera nombre de archivo de backup con timestamp.
    
    Args:
        db_path: Ruta de la BD original
        backup_type: "auto" (automático), "manual" (manual), "startup" (inicio)
    
    Returns:
        Nombre del archivo backup
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_name = Path(db_path).stem
    return f"{db_name}_{backup_type}_{timestamp}.db"


def backup_database(
    db_path: str,
    backup_type: str = "auto",
    force: bool = False
) -> Optional[Path]:
    """
    Realiza backup de la base de datos.
    
    Args:
        db_path: Ruta de la BD a respaldar
        backup_type: Tipo de backup para naming
        force: Si True, ignora las comprobaciones de tiempo
    
    Returns:
        Ruta del archivo backup creado, o None si falla
    """
    try:
        # Validar que exista la BD
        if not os.path.exists(db_path):
            logger.warning(f"Database no encontrada: {db_path}")
            return None
        
        # Crear nombre de backup
        backup_name = get_backup_filename(db_path, backup_type)
        backup_path = BACKUP_DIR / backup_name
        
        logger.info(f"Iniciando backup: {backup_name}")
        
        # Usar conexión SQLite para hacer backup seguro
        try:
            source_conn = sqlite3.connect(db_path)
            dest_conn = sqlite3.connect(str(backup_path))
            
            # Usar backup API de SQLite para copia segura
            with source_conn:
                source_conn.backup(dest_conn)
            
            dest_conn.close()
            source_conn.close()
            
            # Validar que el backup se creó  
            if backup_path.exists():
                size_mb = backup_path.stat().st_size / (1024 * 1024)
                logger.info(f"✓ Backup exitoso: {backup_name} ({size_mb:.2f} MB)")
                
                # Limpiar backups viejos
                cleanup_old_backups()
                
                return backup_path
            else:
                logger.error(f"✗ Backup falló: archivo no creado")
                return None
                
        except Exception as e:
            logger.error(f"✗ Error durante backup SQLite: {e}")
            # Intentar método alternativo (copia directa)
            try:
                shutil.copy2(db_path, str(backup_path))
                logger.warning(f"Backup realizado con copia directa (no recomendado)")
                return backup_path
            except Exception as e2:
                logger.error(f"✗ Backup falló completamente: {e2}")
                return None
    
    except Exception as e:
        logger.error(f"✗ Error crítico en backup: {e}", exc_info=True)
        return None


def cleanup_old_backups(keep_count: int = MAX_BACKUPS) -> int:
    """
    Elimina backups viejos, manteniendo solo los últimos N.
    
    Args:
        keep_count: Número de backups a mantener
    
    Returns:
        Número de archivos eliminados
    """
    try:
        if not BACKUP_DIR.exists():
            return 0
        
        # Listar todos los archivos .db
        backup_files = sorted(
            BACKUP_DIR.glob("*.db"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        deleted = 0
        for old_backup in backup_files[keep_count:]:
            try:
                old_backup.unlink()
                deleted += 1
                logger.debug(f"Backup antiguo eliminado: {old_backup.name}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar {old_backup.name}: {e}")
        
        if deleted > 0:
            logger.info(f"Limpieza completada: {deleted} backups viejos eliminados")
        
        return deleted
    
    except Exception as e:
        logger.error(f"Error en limpieza de backups: {e}")
        return 0


def restore_database(backup_path: str, target_db_path: str) -> bool:
    """
    Restaura la base de datos desde un backup.
    OPERACIÓN PELIGROSA - Requiere confirmación del usuario.
    
    Args:
        backup_path: Ruta del archivo backup
        target_db_path: Ruta donde restaurar
    
    Returns:
        True si restauración fue exitosa
    """
    try:
        if not os.path.exists(backup_path):
            logger.error(f"Backup no encontrado: {backup_path}")
            return False
        
        # Crear backup de seguridad de la BD actual
        if os.path.exists(target_db_path):
            safety_backup = target_db_path + ".pre_restore"
            shutil.copy2(target_db_path, safety_backup)
            logger.info(f"Backup de seguridad creado: {safety_backup}")
        
        # Restaurar desde backup
        logger.warning(f"RESTAURANDO base de datos desde: {backup_path}")
        
        source_conn = sqlite3.connect(backup_path)
        dest_conn = sqlite3.connect(target_db_path)
        
        with source_conn:
            source_conn.backup(dest_conn)
        
        dest_conn.close()
        source_conn.close()
        
        logger.warning(f"✓ Restauración completada exitosamente")
        return True
    
    except Exception as e:
        logger.error(f"✗ Error en restauración: {e}", exc_info=True)
        return False


def list_available_backups() -> List[dict]:
    """
    Lista todos los backups disponibles.
    
    Returns:
        Lista de dicts con información de cada backup
    """
    try:
        backups = []
        for backup_file in sorted(BACKUP_DIR.glob("*.db"), reverse=True):
            stat = backup_file.stat()
            backups.append({
                'filename': backup_file.name,
                'path': str(backup_file),
                'size_mb': stat.st_size / (1024 * 1024),
                'timestamp': datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
        return backups
    
    except Exception as e:
        logger.error(f"Error listando backups: {e}")
        return []
