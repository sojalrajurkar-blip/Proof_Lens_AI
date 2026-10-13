import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database import Base, get_db
from app.main import app
from app.services.embedding_service import embedding_service
from app.core.ai_provider import MockEmbeddingProvider

# Test-isolated in-memory SQLite database
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
test_async_session = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Use deterministic mock embeddings and generation for offline unit/integration test runs
embedding_service.provider = MockEmbeddingProvider()

from app.services.qa_service import qa_service
from app.services.comparison_service import comparison_service
from app.core.ai_provider import MockGenerationProvider
mock_gen = MockGenerationProvider()
qa_service.provider = mock_gen
qa_service.model_name = "mock-generator-v1"
comparison_service.provider = mock_gen
comparison_service.model_name = "mock-generator-v1"


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db() -> AsyncGenerator[None, None]:
    """Create all tables in in-memory test DB before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with test_async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db
