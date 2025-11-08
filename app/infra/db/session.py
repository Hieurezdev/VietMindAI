"""Database session management with PostgreSQL and pgvector support."""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.config import get_settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages PostgreSQL database connections with async support."""

    def __init__(self) -> None:
        """Initialize database manager."""
        self._engine: AsyncEngine | None = None
        self._session_maker: async_sessionmaker[AsyncSession] | None = None

    def get_engine(self) -> AsyncEngine:
        """Get or create the database engine.

        Returns:
            AsyncEngine: SQLAlchemy async engine instance.

        Raises:
            ValueError: If DATABASE_URL is not configured.
        """
        if self._engine is not None:
            return self._engine

        settings = get_settings()
        if not settings.database_url:
            raise ValueError("DATABASE_URL not configured. Please set it in your .env file.")

        self._engine = create_async_engine(
            settings.database_url,
            echo=settings.env == "dev",
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        logger.info("Database engine created successfully")
        return self._engine

    def get_session_maker(self) -> async_sessionmaker[AsyncSession]:
        """Get or create the session maker.

        Returns:
            async_sessionmaker: SQLAlchemy async session maker.
        """
        if self._session_maker is not None:
            return self._session_maker

        engine = self.get_engine()
        self._session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        return self._session_maker

    async def close(self) -> None:
        """Close database connections."""
        if self._engine is not None:
            await self._engine.dispose()
            logger.info("Database connections closed")
            self._engine = None
            self._session_maker = None


# Global database manager instance
_db_manager = DatabaseManager()


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance.

    Returns:
        DatabaseManager: Global database manager instance.
    """
    return _db_manager


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get an async database session.

    Yields:
        AsyncSession: SQLAlchemy async session.

    Example:
        ```python
        from fastapi import Depends
        from app.infra.db.session import get_session

        @router.get("/items")
        async def get_items(session: AsyncSession = Depends(get_session)):
            result = await session.execute(select(Item))
            return result.scalars().all()
        ```
    """
    session_maker = _db_manager.get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
