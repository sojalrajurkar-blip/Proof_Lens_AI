import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

logger = logging.getLogger("prooflens.database")


class Base(DeclarativeBase):
    pass


connect_args = {}
if "postgresql" in settings.DATABASE_URL:
    import ssl
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_ctx

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    connect_args=connect_args,
)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session per request."""
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> bool:
    """Initialize database tables. Returns True if successful, False otherwise."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")
        return True
    except Exception as e:
        logger.warning(
            f"Could not connect to database or initialize tables: {e}. "
            "Please check DATABASE_URL in your .env file."
        )
        return False
