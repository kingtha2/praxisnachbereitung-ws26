import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# DB_DSN aus der Umgebung (docker-compose) hat Vorrang vor alembic.ini.
# SQLAlchemy braucht den Treiber im Schema: postgresql+psycopg://
db_dsn = os.getenv("DB_DSN")
if db_dsn:
    config.set_main_option("sqlalchemy.url", db_dsn.replace("postgresql://", "postgresql+psycopg://", 1))

# Wir arbeiten ohne ORM-Modelle, Migrationen werden von Hand geschrieben.
target_metadata = None


def run_migrations_offline() -> None:
    """Gibt das SQL nur aus (alembic upgrade head --sql)."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
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
