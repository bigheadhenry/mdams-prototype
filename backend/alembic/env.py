from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Alembic Config object
config = context.config

# Logging setup
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import models so that Base.metadata is populated
import sys
from pathlib import Path

# Add backend/ to sys.path so that 'app' can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import DATABASE_URL  # noqa: E402
from app.database import Base  # noqa: E402
from app import models  # noqa: E402, F401 — force model registration

target_metadata = Base.metadata

# Override sqlalchemy.url in config with our app's DATABASE_URL
config.set_main_option("sqlalchemy.url", DATABASE_URL.replace("%", "%%"))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
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
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
