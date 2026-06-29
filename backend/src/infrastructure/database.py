"""
Database configuration and session management
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool, QueuePool

from src.core.config import settings


# Create async engine
def create_engine() -> AsyncEngine:
    """Create database engine with connection pooling"""
    
    engine_kwargs = {
        "echo": settings.DEBUG,
        "future": True,
        "pool_pre_ping": True,
    }
    
    if settings.ENVIRONMENT == "test":
        engine_kwargs["poolclass"] = NullPool
    else:
        engine_kwargs.update({
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_recycle": 3600,
            "pool_timeout": 30,
            "poolclass": QueuePool,
        })
    
    return create_async_engine(
        settings.DATABASE_URL,
        **engine_kwargs
    )


# Create engine instance
engine = create_engine()

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session
    
    Usage in FastAPI:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database - create all tables"""
    from src.domain.models import Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections"""
    await engine.dispose()
