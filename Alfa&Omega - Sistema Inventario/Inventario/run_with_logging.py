#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para capturar y registrar todos los errores que suceden durante login
"""
import sys
import os
import logging
import traceback

# Configurar logging en archivo
log_file = "login_debug.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(__file__))

logger.info("=" * 60)
logger.info("🚀 INICIANDO SISTEMA CON CAPTURA COMPLETA DE ERRORES")
logger.info("=" * 60)

try:
    logger.info("1️⃣ Importando módulos principales...")
    import tkinter as tk
    from src.app.main_window import InventarioApp
    from src.database.connection import init_db
    from src.core.auth import ensure_defaults
    logger.info("   ✅ Módulos importados correctamente")
    
    logger.info("2️⃣ Inicializando base de datos...")
    init_db()
    ensure_defaults()
    logger.info("   ✅ Base de datos lista")
    
    logger.info("3️⃣ Creando ventana principal...")
    root = tk.Tk()
    logger.info("   ✅ Ventana Tkinter creada")
    
    logger.info("4️⃣ Iniciando aplicación Inventario...")
    try:
        app = InventarioApp(root)
        logger.info("   ✅ Aplicación creada exitosamente")
        logger.info("   ℹ️  El diálogo de login debería estar visible")
    except Exception as e:
        logger.error(f"   ❌ Error creando aplicación: {e}")
        logger.error(f"   Traceback: {traceback.format_exc()}")
        raise
    
    logger.info("5️⃣ Iniciando loop de eventos Tkinter...")
    root.mainloop()
    logger.info("   ℹ️  Aplicación cerrada por el usuario")
    
except Exception as e:
    logger.error(f"❌ ERROR CRÍTICO: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    sys.exit(1)

logger.info("=" * 60)
logger.info("✅ Sistema cerrado correctamente")
logger.info(f"ℹ️  Ver {log_file} para detalles completos")
