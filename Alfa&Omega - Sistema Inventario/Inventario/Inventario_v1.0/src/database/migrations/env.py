"""Alembic environment for migrations.
Reads `DATABASE_URL` from .env and uses ORM metadata from `src.database.models`.
"""
from __future__ import annotations
import os
import sys
from logging.config import fileConfig
from dotenv import load_dotenv

load_dotenv()

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy import create_engine

# add src to path so imports work when running alembic from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import metadata
from src.database.models import Base

target_metadata = Base.metadata

# Use DATABASE_URL from environment; Alembic prefers a sync driver
database_url = os.getenv('DATABASE_URL')
if not database_url:
    raise RuntimeError('DATABASE_URL is not set in environment or .env')

# Convert async drivers to sync equivalents for Alembic
sync_url = database_url
if '+asyncpg' in sync_url:
    sync_url = sync_url.replace('+asyncpg', '+psycopg2')
elif '+aiosqlite' in sync_url:
    # aiosqlite -> sqlite
    sync_url = sync_url.replace('+aiosqlite', '')

config.set_main_option('sqlalchemy.url', sync_url)

def run_migrations_offline():
    url = config.get_main_option('sqlalchemy.url')
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
