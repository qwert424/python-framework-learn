from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 从项目配置中读取数据库连接信息
from app.core.config import db_settings

# 导入模型（通过 __init__.py 触发所有模型注册到 Base.metadata）
from app.model.base import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
# Alembic 配置对象，用于读取 alembic.ini
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
# 配置 Python 日志（读取 alembic.ini 中的 [loggers] 配置）
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# 用项目配置覆盖 alembic.ini 中的 sqlalchemy.url
# 使用同步驱动 postgresql://（不需要 +asyncpg）
config.set_main_option(
    "sqlalchemy.url",
    f"postgresql://{db_settings.user}:{db_settings.password}@{db_settings.host}:{db_settings.port}/{db_settings.name}",
)
# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# 告诉 Alembic 你的模型元数据，用于自动生成迁移
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
# 其他配置项可通过 config.get_main_option() 获取


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    """离线模式执行迁移（只生成 SQL 脚本，不连接数据库）"""
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
    """在线模式执行迁移（直接连接数据库执行）"""

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
