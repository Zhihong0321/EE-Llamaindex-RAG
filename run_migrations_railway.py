"""Run database migrations on Railway production database.

This script connects to the Railway database and runs pending Alembic migrations.
"""
import asyncio
import os
from alembic.config import Config
from alembic import command


def run_migrations():
    """Run Alembic migrations."""
    # Get database URL from environment
    db_url = os.getenv("DATABASE_URL") or os.getenv("DB_URL")
    
    if not db_url:
        print("ERROR: DATABASE_URL or DB_URL environment variable not set")
        return
    
    print(f"Running migrations on: {db_url[:30]}...")
    
    # Create Alembic config
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    
    # Run migrations
    try:
        print("Running: alembic upgrade head")
        command.upgrade(alembic_cfg, "head")
        print("✓ Migrations completed successfully")
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        raise


if __name__ == "__main__":
    run_migrations()
