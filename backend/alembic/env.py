import os
from logging.config import fileConfig
from alembic import context
from sqlalchemy import create_engine, pool
from dotenv import load_dotenv
from app.db.base import Base
import app.models  # noqa: F401 - register models

load_dotenv()
config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata


def include_object(obj, name, type_, reflected, compare_to):
    # PostGIS owns this table; Pathways must never generate a DROP for it.
    return not (type_ == "table" and reflected and compare_to is None and name == "spatial_ref_sys")


def run_migrations_offline():
    url = os.environ.get("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
    context.configure(url=url, target_metadata=target_metadata, include_object=include_object, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    url = os.environ.get("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True, include_object=include_object)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
