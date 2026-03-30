import os
import tempfile
import shutil
import pytest
import asyncio
from pathlib import Path

import importlib
import src.database.connection as dbconn

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.database.models import Base


@pytest.fixture(scope='session')
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
def temp_db_dir():
    d = tempfile.mkdtemp(prefix='inventario_tests_')
    yield d
    shutil.rmtree(d)


@pytest.fixture(scope='function', autouse=True)
def use_temp_db(temp_db_dir):
    # create a temp sqlite file unique per test (function scope)
    import uuid
    db_path = os.path.join(temp_db_dir, f"test_inventario_{uuid.uuid4().hex}.db")
    # set env so modules that read env at import time will pick it up
    os.environ['DB_ENGINE'] = 'sqlite'
    os.environ['DB_PATH'] = db_path
    # reload the db connection module so it reads the updated env vars
    importlib.reload(dbconn)
    # Also reload orm module to pick up new DB_ENGINE
    import src.database.orm
    importlib.reload(src.database.orm)
    # ensure db exists
    dbconn.init_db()
    try:
        yield
    finally:
        try:
            os.remove(db_path)
        except Exception:
            pass


@pytest.fixture
def db_session(event_loop, temp_db_dir):
    """Provide a test async database session with fresh schema.
    
    This is a sync fixture that yields an async session factory.
    Tests must be async to use this fixture.
    """
    import uuid
    
    db_path = Path(temp_db_dir) / f"test_async_{uuid.uuid4().hex}.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    
    # Setup: create engine and tables
    async def setup():
        engine = create_async_engine(
            db_url,
            echo=False,
            future=True,
        )
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        return engine, async_session
    
    # Run setup
    engine, async_session = event_loop.run_until_complete(setup())
    
    # Yield session factory
    yield async_session
    
    # Teardown
    async def teardown():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()
    
    event_loop.run_until_complete(teardown())
    
    # Remove temp DB file
    try:
        if db_path.exists():
            db_path.unlink()
    except Exception:
        pass
