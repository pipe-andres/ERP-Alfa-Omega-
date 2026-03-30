#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para capturar TODOS los errores sin importar dónde ocurran
"""
import sys
import os
import logging
import traceback

# Configurar logging muy detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("error_captura.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Instalar manejador de excepciones no capturadas
def excepthook(exc_type, exc_value, exc_traceback):
    logger.error("EXCEPCIÓN NO CAPTURADA:", exc_info=(exc_type, exc_value, exc_traceback))
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = excepthook

sys.path.insert(0, os.path.dirname(__file__))

logger.info("=" * 70)
logger.info("🚀 INICIANDO SISTEMA CON CAPTURA TOTAL DE ERRORES")
logger.info("=" * 70)

try:
    logger.info("\n1️⃣ Importando módulos...")
    import tkinter as tk
    from src.app.main_window import InventarioApp
    from src.database.connection import init_db
    from src.core.auth import ensure_defaults
    logger.info("   ✅ Imports OK")
    
    logger.info("\n2️⃣ Inicializando BD...")
    init_db()
    ensure_defaults()
    logger.info("   ✅ BD OK")
    
    logger.info("\n3️⃣ Creando root...")
    root = tk.Tk()
    logger.info("   ✅ Root OK")
    
    logger.info("\n4️⃣ Creando InventarioApp...")
    app = InventarioApp(root)
    logger.info("   ✅ App OK - Si no ves esta línea, error en __init__")
    
    logger.info("\n5️⃣ Iniciando mainloop...")
    root.mainloop()
    logger.info("   ℹ️  App cerrada por usuario")
    
except Exception as e:
    logger.error(f"\n❌ EXCEPCIÓN CAPTURADA: {e}")
    logger.error(f"Traceback completo:\n{traceback.format_exc()}")
    sys.exit(1)

logger.info("\n" + "=" * 70)
logger.info("✅ Programa terminado normalmente")
logger.info(f"📋 Ver error_captura.log para detalles completos")
