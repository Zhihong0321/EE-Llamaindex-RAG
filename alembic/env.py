"""Alembic environment configuration for synchronous migrations."""

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = None

# Override sqlalchemy.url with environment variable if available
# Try DB_URL first, then fall back to DATABASE_URL (Railway default)
db_url = os.getenv("DB_URL") or os.getenv("DATABASE_URL")

if db_url:
    # Convert async URL to sync URL for Alembic
    # postgresql+asyncpg:// -> postgresql+psycopg2://
    # postgresql:// -> postgresql+psycopg2://
    if "+asyncpg" in db_url:
        db_url = db_url.replace("+asyncpg", "+psycopg2")
    elif db_url.startswith("postgresql://") and "+psycopg2" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    elif db_url.startswith("postgres://"):
        # Railway uses postgres:// which needs to be converted
        db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    
    config.set_main_option("sqlalchemy.url", db_url)
else:
    raise ValueError(
        "Database URL not found. Please set DB_URL or DATABASE_URL environment variable."
    )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using synchronous engine.
    
    Alembic works better with synchronous engines, so we use
    psycopg2 instead of asyncpg for migrations.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()
    
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
