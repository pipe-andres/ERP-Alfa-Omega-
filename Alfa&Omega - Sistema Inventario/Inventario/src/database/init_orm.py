"""Helper to initialize ORM metadata on the configured database.

This script performs `Base.metadata.create_all()` using the async engine.
Useful for smoke tests or for environments where Alembic is not yet used.
"""
from __future__ import annotations
import asyncio
from src.database.orm import get_engine
from src.database.models import Base

async def init_models():
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == '__main__':
    asyncio.run(init_models())
