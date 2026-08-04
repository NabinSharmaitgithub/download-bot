from contextlib import asynccontextmanager
from typing import AsyncGenerator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _sanitize_database_url(url: str) -> tuple[str, str | None]:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    sslmode = query_params.pop("sslmode", [None])[0]

    new_query = urlencode(query_params, doseq=True)
    url = urlunparse(parsed._replace(query=new_query))

    if not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return url, sslmode


class Database:
    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def initialize(self) -> None:
        settings = get_settings()
        db_url, sslmode = _sanitize_database_url(str(settings.database_url))

        connect_args = {}

        if sslmode in ("require", "verify-ca", "verify-full"):
            connect_args["ssl"] = True

        if settings.is_testing:
            engine = create_async_engine(
                db_url.replace("postgresql+asyncpg", "sqlite+aiosqlite"),
                poolclass=NullPool,
                echo=settings.debug,
            )
        else:
            engine = create_async_engine(
                db_url,
                pool_size=settings.database_pool_size,
                max_overflow=settings.database_max_overflow,
                pool_timeout=settings.database_pool_timeout,
                pool_recycle=settings.database_pool_recycle,
                echo=settings.debug,
                connect_args=connect_args,
            )

        self._engine = engine
        self._session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        logger.info("database_initialized", pool_size=settings.database_pool_size)

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._session_factory

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def close(self) -> None:
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("database_closed")


database = Database()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with database.session() as session:
        yield session
