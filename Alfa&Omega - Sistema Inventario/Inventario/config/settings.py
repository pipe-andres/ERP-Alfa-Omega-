import os
from pathlib import Path

# try to load .env file if present
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path)
except ImportError:  # dotenv is optional
    pass

# environment (dev or prod)
ENV = os.getenv("ENV", "dev").lower()
DEBUG = os.getenv("DEBUG", "1" if ENV == "dev" else "0") in ("1", "true", "True")

# database settings
DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").lower()
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "src" / "data")))
DB_PATH = Path(os.getenv("DB_PATH", str(DATA_DIR / "inventario.db")))
DB_JSON_DIR = Path(os.getenv("DB_JSON_DIR", str(DATA_DIR)))

# network
PORT = int(os.getenv("PORT", "8000"))

# logging and filesystem
LOG_DIR = Path(os.getenv("LOG_DIR", str(BASE_DIR / "logs")))
BACKUP_DIR = Path(os.getenv("BACKUP_DIR", str(BASE_DIR / "backups")))
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG" if DEBUG else "INFO")

# other flags
USE_CACHE = os.getenv("USE_CACHE", "0") in ("1", "true", "True")

# ensure directories exist
for p in (DATA_DIR, LOG_DIR, BACKUP_DIR):
    try:
        p.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
