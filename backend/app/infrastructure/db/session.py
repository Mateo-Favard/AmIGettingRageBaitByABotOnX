from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings


@lru_cache
def _get_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        settings.database_url.get_secret_value(),
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
        echo=False,
    )


@lru_cache
def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        _get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    session_factory = _get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
