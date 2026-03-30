"""Utilities to initialize the database during installation or first run."""

import sys
from pathlib import Path

# add workspace src to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.database.connection import init_db
from src.database.create_indexes import create_indexes
from src.database.settings import ensure_schema as ensure_settings_schema


def main():
    print("Starting database setup...")
    # Create schema and default settings
    init_db()
    ensure_settings_schema()
    # build indexes
    if create_indexes():
        print("Indexes created successfully.")
    else:
        print("Some indexes failed to create; check logs.")

    print("Database setup complete.")


if __name__ == "__main__":
    main()
