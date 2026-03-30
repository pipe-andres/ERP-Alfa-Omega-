"""FastAPI y SQLAlchemy configuration."""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # FastAPI
    app_title: str = "Alfa & Omega - Sistema Inventario API"
    app_version: str = "2.0.0"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Database
    db_engine: str = os.getenv("DB_ENGINE", "sqlite")
    db_path: Optional[str] = os.getenv("DB_PATH", None)
    
    # Inventory
    inventory_cost_policy: str = os.getenv("INVENTORY_COST_POLICY", "fifo")
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        extra = "ignore"


settings = Settings()


def get_database_url() -> str:
    """Get the database URL from settings."""
    if settings.db_engine == "sqlite":
        db_path = settings.db_path or "./data/inventario_temp.db"
        return f"sqlite+aiosqlite:///{db_path}"
    
    raise ValueError(f"Unsupported database engine: {settings.db_engine}")
