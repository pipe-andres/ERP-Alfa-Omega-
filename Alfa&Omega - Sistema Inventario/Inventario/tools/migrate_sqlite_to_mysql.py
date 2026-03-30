#!/usr/bin/env python3
"""Script simple para migrar datos desde SQLite a MySQL.

Uso:
  - Asegúrate de tener MySQL corriendo y las credenciales en las variables de entorno:
      DB_ENGINE=mysql
      DB_HOST, DB_USER, DB_PASS, DB_NAME
  - Instala dependencias: `pip install mysql-connector-python`
  - Ejecuta: `python tools/migrate_sqlite_to_mysql.py`

Este script crea un esquema básico en MySQL (si no existe) y copia filas desde el
archivo SQLite apuntado por la variable `DB_PATH` o `data/inventario.db`.

Nota: revisa el DDL generado y haz backup antes de ejecutar en producción.
"""
import os
import sqlite3
import sys
import logging

try:
    import mysql.connector
except Exception as e:
    logging.getLogger(__name__).error("Falta mysql-connector-python. Instálalo con: pip install mysql-connector-python")
    raise

# Config
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.getenv("DB_PATH", os.path.join(DATA_DIR, "inventario.db"))

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_NAME = os.getenv("DB_NAME", "inventario")

def ensure_mysql_database(conn, name):
    cur = conn.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    conn.commit()

def create_mysql_schema(conn):
    cur = conn.cursor()
    # Simplified DDL. Ajustar según necesites.
    cur.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        codigo VARCHAR(200) NOT NULL UNIQUE,
        nombre TEXT NOT NULL,
        categoria VARCHAR(200),
        precio DOUBLE NOT NULL DEFAULT 0,
        cantidad INT NOT NULL DEFAULT 0,
        avg_cost DOUBLE NOT NULL DEFAULT 0
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS partners (
        id INT AUTO_INCREMENT PRIMARY KEY,
        code VARCHAR(200) UNIQUE NOT NULL,
        kind VARCHAR(20) NOT NULL,
        name TEXT NOT NULL,
        tax_id VARCHAR(100),
        phone VARCHAR(100),
        email VARCHAR(200),
        address TEXT,
        city VARCHAR(100),
        notes TEXT,
        active TINYINT(1) NOT NULL DEFAULT 1
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(200) UNIQUE NOT NULL,
        name TEXT NOT NULL,
        pass_hash TEXT NOT NULL,
        active TINYINT(1) NOT NULL DEFAULT 1
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(200) UNIQUE NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS permissions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        code VARCHAR(200) UNIQUE NOT NULL,
        description TEXT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_roles (
        user_id INT NOT NULL,
        role_id INT NOT NULL,
        PRIMARY KEY (user_id, role_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS role_permissions (
        role_id INT NOT NULL,
        perm_id INT NOT NULL,
        PRIMARY KEY (role_id, perm_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        action VARCHAR(200) NOT NULL,
        details TEXT,
        created_at VARCHAR(50) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # documents, document_lines, stock_movements, historial, doc_series simplified
    cur.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INT AUTO_INCREMENT PRIMARY KEY,
        tipo VARCHAR(20) NOT NULL,
        numero VARCHAR(200),
        fecha VARCHAR(50) NOT NULL,
        notas TEXT,
        partner_id INT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS document_lines (
        id INT AUTO_INCREMENT PRIMARY KEY,
        doc_id INT NOT NULL,
        codigo VARCHAR(200) NOT NULL,
        qty DOUBLE NOT NULL,
        unit_cost DOUBLE,
        unit_price DOUBLE,
        reason TEXT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS stock_movements (
        id INT AUTO_INCREMENT PRIMARY KEY,
        doc_id INT,
        codigo VARCHAR(200) NOT NULL,
        qty DOUBLE NOT NULL,
        unit_cost DOUBLE,
        unit_price DOUBLE,
        tipo VARCHAR(20) NOT NULL,
        reason TEXT,
        created_at VARCHAR(50) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS doc_series (
        id INT AUTO_INCREMENT PRIMARY KEY,
        doc_type VARCHAR(20) NOT NULL,
        series VARCHAR(50) NOT NULL,
        prefix VARCHAR(50),
        next_no INT NOT NULL DEFAULT 1,
        UNIQUE(doc_type, series)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS historial (
        id INT AUTO_INCREMENT PRIMARY KEY,
        codigo VARCHAR(200),
        nombre TEXT,
        accion TEXT,
        fecha TEXT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    conn.commit()

def copy_table(scur, mcur, table, cols, placeholder=None):
    placeholder = placeholder or ("%s," * len(cols))[:-1]
    scur.execute(f"SELECT {', '.join(cols)} FROM {table}")
    rows = scur.fetchall()
    if not rows:
        logging.getLogger(__name__).info("No hay filas en %s", table)
        return 0
    inserted = 0
    for r in rows:
        try:
            mcur.execute(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholder})", tuple(r))
            inserted += 1
        except Exception as e:
            # ignorar filas duplicadas o errores puntuales
            logging.getLogger(__name__).warning("No pude insertar en %s: %s", table, e)
    return inserted

def main():
    if not os.path.exists(DB_PATH):
        logging.getLogger(__name__).error("Archivo SQLite no encontrado en: %s", DB_PATH)
        sys.exit(1)
    logging.getLogger(__name__).info("Conectando a MySQL en %s", DB_HOST)
    root_conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS)
    ensure_mysql_database(root_conn, DB_NAME)
    root_conn.close()

    mconn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)
    create_mysql_schema(mconn)
    mcur = mconn.cursor()

    scon = sqlite3.connect(DB_PATH)
    scur = scon.cursor()

    tables = [
        ("roles", ["name"]),
        ("permissions", ["code","description"]),
        ("users", ["username","name","pass_hash","active"]),
        ("user_roles", ["user_id","role_id"]),
        ("role_permissions", ["role_id","perm_id"]),
        ("productos", ["codigo","nombre","categoria","precio","cantidad","avg_cost"]),
        ("partners", ["code","kind","name","tax_id","phone","email","address","city","notes","active"]),
        ("audit_log", ["user_id","action","details","created_at"]),
        ("documents", ["tipo","numero","fecha","notas","partner_id"]),
        ("document_lines", ["doc_id","codigo","qty","unit_cost","unit_price","reason"]),
        ("stock_movements", ["doc_id","codigo","qty","unit_cost","unit_price","tipo","reason","created_at"]),
        ("doc_series", ["doc_type","series","prefix","next_no"]),
        ("historial", ["codigo","nombre","accion","fecha"]),
    ]

    total = 0
    for tbl, cols in tables:
        logging.getLogger(__name__).info("Copiando %s...", tbl)
        try:
            cnt = copy_table(scur, mcur, tbl, cols)
            mconn.commit()
            logging.getLogger(__name__).info("  Insertadas: %d", cnt)
            total += cnt
        except Exception as e:
            logging.getLogger(__name__).error("Error copiando %s: %s", tbl, e)

    scon.close()
    mcur.close()
    mconn.close()

    logging.getLogger(__name__).info("Migración completada. Filas copiadas aproximadamente: %d", total)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    main()
