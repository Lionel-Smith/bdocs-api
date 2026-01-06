"""
Alembic migration environment for BDOCS.

Configured for async SQLAlchemy with PostgreSQL.
"""
import sys
import importlib.util
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load async_db module directly without triggering src/__init__.py
# This avoids the create_app import that requires quart_auth
async_db_path = project_root / "src" / "database" / "async_db.py"
spec = importlib.util.spec_from_file_location("async_db", async_db_path)
async_db = importlib.util.module_from_spec(spec)
spec.loader.exec_module(async_db)
AsyncBase = async_db.AsyncBase

# Load enums module directly
enums_path = project_root / "src" / "common" / "enums.py"
spec = importlib.util.spec_from_file_location("enums", enums_path)
enums = importlib.util.module_from_spec(spec)
spec.loader.exec_module(enums)
sys.modules['src.common.enums'] = enums  # Make it available for imports

# Setup fake module entries for imports
sys.modules['src.database.async_db'] = type(sys)('src.database.async_db')
sys.modules['src.database.async_db'].AsyncBase = AsyncBase

# Load mixins module
mixins_path = project_root / "src" / "models" / "mixins.py"
spec = importlib.util.spec_from_file_location("mixins", mixins_path)
mixins = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mixins)
sys.modules['src.models.mixins'] = mixins

# Load audit_log_model module directly
audit_log_path = project_root / "src" / "models" / "audit_log_model.py"
spec = importlib.util.spec_from_file_location("audit_log_model", audit_log_path)
audit_log_model = importlib.util.module_from_spec(spec)
audit_log_model.AsyncBase = AsyncBase
spec.loader.exec_module(audit_log_model)

# Load Inmate model module
inmate_models_path = project_root / "src" / "modules" / "inmate" / "models.py"
spec = importlib.util.spec_from_file_location("inmate_models", inmate_models_path)
inmate_models = importlib.util.module_from_spec(spec)
inmate_models.AsyncBase = AsyncBase
spec.loader.exec_module(inmate_models)

# Load Housing models module
housing_models_path = project_root / "src" / "modules" / "housing" / "models.py"
spec = importlib.util.spec_from_file_location("housing_models", housing_models_path)
housing_models = importlib.util.module_from_spec(spec)
housing_models.AsyncBase = AsyncBase
spec.loader.exec_module(housing_models)

# Load Movement models module
movement_models_path = project_root / "src" / "modules" / "movement" / "models.py"
spec = importlib.util.spec_from_file_location("movement_models", movement_models_path)
movement_models = importlib.util.module_from_spec(spec)
movement_models.AsyncBase = AsyncBase
spec.loader.exec_module(movement_models)

# Load Court models module
court_models_path = project_root / "src" / "modules" / "court" / "models.py"
spec = importlib.util.spec_from_file_location("court_models", court_models_path)
court_models = importlib.util.module_from_spec(spec)
court_models.AsyncBase = AsyncBase
spec.loader.exec_module(court_models)

# Load Sentence models module
sentence_models_path = project_root / "src" / "modules" / "sentence" / "models.py"
spec = importlib.util.spec_from_file_location("sentence_models", sentence_models_path)
sentence_models = importlib.util.module_from_spec(spec)
sentence_models.AsyncBase = AsyncBase
spec.loader.exec_module(sentence_models)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use AsyncBase metadata for autogenerate support
target_metadata = AsyncBase.metadata


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
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
