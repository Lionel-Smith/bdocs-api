from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager
from config import FLASK_ENV, PostgresDB

# Async PostgreSQL engine
async_pg_engine = None
async_session_maker = None

# Declarative base for async models
AsyncBase = declarative_base()


async def init_db():
    """Initialize async database connections"""
    global async_pg_engine, async_session_maker

    # Build PostgreSQL async URL
    postgres_url = f"postgresql+asyncpg://{PostgresDB.username}:{PostgresDB.password}@{PostgresDB.host}:{PostgresDB.port}/{PostgresDB.database}"

    # PostgreSQL async engine
    async_pg_engine = create_async_engine(
        postgres_url,
        echo=FLASK_ENV == "development",
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True
    )

    async_session_maker = async_sessionmaker(
        async_pg_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # Create tables if they don't exist
    async with async_pg_engine.begin() as conn:
        await conn.run_sync(AsyncBase.metadata.create_all)


async def close_db():
    """Close database connections"""
    global async_pg_engine
    if async_pg_engine:
        await async_pg_engine.dispose()


@asynccontextmanager
async def get_async_session() -> AsyncSession:
    """Dependency for getting async database session"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
