import logging
from logging.config import fileConfig
import os
import sys
from urllib.parse import urlsplit

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Prefer DIRECT_DATABASE_URL (non-pooled) for migrations - Supabase's transaction
# pooler (port 6543) doesn't reliably support the prepared statements/DDL Alembic
# issues. Falls back to SUPABASE_DB_URL (same URL the app uses) if unset.
direct_database_url = os.getenv("DIRECT_DATABASE_URL")
database_url = direct_database_url or os.getenv("SUPABASE_DB_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)
    source = "DIRECT_DATABASE_URL" if direct_database_url else "SUPABASE_DB_URL (fallback)"
    parsed = urlsplit(database_url)
    logger.info(
        "alembic: using %s -> host=%s port=%s (password redacted)",
        source, parsed.hostname, parsed.port,
    )
from app.models import Base
target_metadata = Base.metadata


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
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()